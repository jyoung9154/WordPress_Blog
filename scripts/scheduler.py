#!/usr/bin/env python3
# ==============================================================================
# 스케줄러 스크립트
# ==============================================================================
# 이 파일의 역할: 전체 파이프라인 실행을 스케줄링하고 모니터링
# 사용법: python scripts/scheduler.py --start  # 스케줄러 시작
#        python scripts/scheduler.py --run-once  # 한 번만 실행
#        python scripts/scheduler.py --status  # 상태 확인
# ==============================================================================

import sys
import os
import json
import argparse
import schedule
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    load_environment,
    setup_logging,
    load_json,
    save_json,
    list_output_files,
    generate_timestamp,
    ROOT_DIR,
    LOGS_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("scheduler", "scheduler.log")

# ==============================================================================
# 상수 정의
# ==============================================================================
STATUS_FILE = LOGS_DIR / "scheduler_status.json"
SCHEDULE_DAYS = ["mon", "wed", "fri"]  # 기본 스케줄 (월, 수, 금)
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 0

# ==============================================================================
# 상태 관리
# ==============================================================================
def load_status() -> Dict[str, Any]:
    """
    스케줄러 상태를 로드합니다.
    
    Returns:
        상태 딕셔너리
    """
    if STATUS_FILE.exists():
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "running": False,
        "last_run": None,
        "next_run": None,
        "total_runs": 0,
        "successful_runs": 0,
        "failed_runs": 0,
        "posts_generated": 0,
        "posts_published": 0
    }

def save_status(status: Dict[str, Any]) -> bool:
    """
    스케줄러 상태를 저장합니다.
    
    Args:
        status: 상태 딕셔너리
    
    Returns:
        저장 성공 여부
    """
    try:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"상태 저장 실패: {e}")
        return False

# ==============================================================================
# 파이프라인 실행 함수
# ==============================================================================
def run_pipeline_step(step_name: str, step_func, *args, **kwargs) -> Any:
    """
    파이프라인의 단일 스텝을 실행합니다.
    
    Args:
        step_name: 스텝 이름
        step_func: 실행할 함수
        *args, **kwargs: 함수 인자
    
    Returns:
        실행 결과
    """
    logger.info(f"[파이프라인] {step_name} 시작")
    
    try:
        result = step_func(*args, **kwargs)
        logger.info(f"[파이프라인] {step_name} 완료")
        return result
    except Exception as e:
        logger.error(f"[파이프라인] {step_name} 실패: {e}")
        raise

def run_full_pipeline() -> bool:
    """
    전체 파이프라인을 실행합니다.
    
    Returns:
        성공 여부
    """
    logger.info("="*60)
    logger.info("전체 파이프라인 실행 시작")
    logger.info("="*60)
    
    start_time = datetime.now()
    status = load_status()
    
    try:
        # 1단계: 글 생성
        logger.info("[1/5] AI 글 생성 단계")
        from scripts.generate_post import generate_post, select_keyword_by_priority
        
        topics_data = load_json("topics.json")
        keyword_info = select_keyword_by_priority(topics_data)
        
        if not keyword_info:
            logger.error("키워드 선택 실패")
            return False
        
        post_data = generate_post(keyword_info)
        if not post_data:
            logger.error("글 생성 실패")
            return False
        
        # 생성된 파일명
        slug = post_data.get("slug", "post")
        safe_slug = slug[:50]
        filename = f"post_{generate_timestamp()}_{safe_slug}.json"
        save_json(post_data, filename)
        
        status["posts_generated"] += 1
        logger.info(f"글 생성 완료: {filename}")
        
        # 2단계: SEO 최적화
        logger.info("[2/5] SEO 최적화 단계")
        from scripts.seo_optimizer import optimize_seo
        
        optimized_result = optimize_seo(post_data)
        optimized_data = optimized_result["optimized_data"]
        
        optimized_filename = filename.replace(".json", "_optimized.json")
        save_json(optimized_data, optimized_filename)
        
        logger.info(f"SEO 최적화 완료: {optimized_filename}")
        
        # 3단계: 제휴링크 삽입
        logger.info("[3/5] 제휴링크 삽입 단계")
        from scripts.affiliate_inserter import AffiliateInserter
        
        affiliates_config = load_json("affiliates.json")
        inserter = AffiliateInserter(affiliates_config)
        final_data = inserter.process_post(optimized_data)
        
        final_filename = optimized_filename.replace(".json", "_affiliate.json")
        save_json(final_data, final_filename)
        
        logger.info(f"제휴링크 삽입 완료: {final_filename}")
        
        # 4단계: 검토 대기열에 추가 (자동 발행 없이)
        logger.info("[4/5] 검토 대기열 추가 완료")
        logger.info(f"생성된 포스트: output/{final_filename}")
        logger.info("검토 노드에서 확인 후 발행해주세요: python scripts/review_queue.py")
        
        # 5단계: 상태 업데이트
        logger.info("[5/5] 상태 업데이트")
        status["last_run"] = datetime.now().isoformat()
        status["total_runs"] += 1
        status["successful_runs"] += 1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"파이프라인 완료! 소요 시간: {elapsed:.1f}초")
        
        save_status(status)
        return True
        
    except Exception as e:
        logger.error(f"파이프라인 실행 중 오류: {e}")
        status["total_runs"] += 1
        status["failed_runs"] += 1
        status["last_run"] = datetime.now().isoformat()
        save_status(status)
        return False

def run_scheduled_job():
    """
    스케줄된 작업을 실행합니다. (스레드에서 실행)
    """
    logger.info("스케줄된 작업 시작")
    
    # 이미 실행 중인지 확인
    status = load_status()
    if status.get("running"):
        logger.warning("이전 작업이 아직 실행 중입니다. 건너뜁니다.")
        return
    
    # 실행 중 상태로 업데이트
    status["running"] = True
    save_status(status)
    
    try:
        run_full_pipeline()
    finally:
        status = load_status()
        status["running"] = False
        save_status(status)

# ==============================================================================
# 스케줄러 관리
# ==============================================================================
def setup_schedule():
    """
    스케줄을 설정합니다.
    """
    # 매일 실행 시간 설정
    schedule.every().day.at(f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}").do(run_scheduled_job)
    
    # 주간 스케줄 (지정된 요일만)
    for day in SCHEDULE_DAYS:
        getattr(schedule.every(), day).at(f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}").do(run_scheduled_job)
    
    logger.info(f"스케줄 설정 완료: {', '.join(SCHEDULE_DAYS)} {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")

def run_scheduler():
    """
    스케줄러를 실행합니다.
    """
    logger.info("스케줄러를 시작합니다...")
    
    # 스케줄 설정
    setup_schedule()
    
    # 상태 업데이트
    status = load_status()
    status["running"] = True
    save_status(status)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        logger.info("스케줄러를 종료합니다...")
        status = load_status()
        status["running"] = False
        save_status(status)

def print_status():
    """
    현재 상태를 출력합니다.
    """
    status = load_status()
    
    print(f"\n{'='*60}")
    print(f"📊 스케줄러 상태")
    print(f"{'='*60}")
    print(f"실행 상태: {'🟢 실행 중' if status.get('running') else '🔴 중지됨'}")
    print(f"총 실행 횟수: {status.get('total_runs', 0)}")
    print(f"성공: {status.get('successful_runs', 0)}")
    print(f"실패: {status.get('failed_runs', 0)}")
    print(f"생성된 포스트: {status.get('posts_generated', 0)}")
    print(f"발행된 포스트: {status.get('posts_published', 0)}")
    
    if status.get("last_run"):
        last_run = datetime.fromisoformat(status["last_run"])
        print(f"마지막 실행: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n스케줄: {', '.join(SCHEDULE_DAYS)} {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
    print(f"{'='*60}\n")

def print_dashboard():
    """
    발행 현황 대시보드를 출력합니다.
    """
    # 로그 파일에서 정보 수집
    review_logs = []
    log_file = LOGS_DIR / "review_log.json"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            review_logs = json.load(f)
    
    # 월간 리포트
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    
    monthly_logs = [
        log for log in review_logs 
        if datetime.fromisoformat(log["timestamp"]) >= month_start
    ]
    
    approved = sum(1 for log in monthly_logs if log["action"] == "approved")
    rejected = sum(1 for log in monthly_logs if log["action"] == "rejected")
    skipped = sum(1 for log in monthly_logs if log["action"] == "skipped")
    
    print(f"\n{'='*60}")
    print(f"📈 월간 리포트 ({now.strftime('%Y년 %m월')})")
    print(f"{'='*60}")
    print(f"검토된 포스트: {len(monthly_logs)}")
    print(f"  - 승인: {approved}")
    print(f"  - 거부: {rejected}")
    print(f"  - 건너뜀: {skipped}")
    
    # 출력 폴더의 파일 수
    output_files = list_output_files()
    pending = [f for f in output_files if '_published' not in f and '_optimized' not in f and '_affiliate' not in f]
    
    print(f"\n대기열 현황:")
    print(f"  - 검토 대기: {len(pending)}")
    print(f"  - 총 생성됨: {len(output_files)}")
    
    print(f"{'='*60}\n")

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="파이프라인 스케줄러를 관리합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/scheduler.py --start       # 스케줄러 시작
  python scripts/scheduler.py --run-once    # 한 번만 실행
  python scripts/scheduler.py --status      # 상태 확인
  python scripts/scheduler.py --dashboard   # 대시보드 출력
        """
    )
    
    parser.add_argument("--start", action="store_true", help="스케줄러를 백그라운드에서 시작")
    parser.add_argument("--run-once", action="store_true", help="파이프라인을 한 번만 실행")
    parser.add_argument("--status", action="store_true", help="현재 상태 출력")
    parser.add_argument("--dashboard", action="store_true", help="발행 현황 대시보드 출력")
    
    args = parser.parse_args()
    
    # 환경변수 로드
    load_environment()
    
    if args.status:
        print_status()
    elif args.dashboard:
        print_dashboard()
    elif args.run_once:
        print("파이프라인을 한 번 실행합니다...")
        run_full_pipeline()
    elif args.start:
        print("스케줄러를 시작합니다. 종료하려면 Ctrl+C를 누르세요.")
        print(f"스케줄: {', '.join(SCHEDULE_DAYS)} {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}")
        run_scheduler()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()