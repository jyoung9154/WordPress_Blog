#!/usr/bin/env python3
# ==============================================================================
# 검토 노드 스크립트
# ==============================================================================
# 이 파일의 역할: 생성된 포스트를 터미널에서 검토하고 승인/거부/재생성 처리
# 사용법: python scripts/review_queue.py
#        python scripts/review_queue.py --web  # 웹 UI 모드
# ==============================================================================

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    load_environment,
    setup_logging,
    load_json,
    save_json,
    load_output_json,
    list_output_files,
    generate_timestamp,
    ROOT_DIR,
    LOGS_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("review_queue", "review_queue.log")

# ==============================================================================
# 상수 정의
# ==============================================================================
REVIEW_LOG_FILE = LOGS_DIR / "review_log.json"

# ==============================================================================
# 검토 로그 관리
# ==============================================================================
def load_review_log() -> list:
    """
    검토 로그 파일을 로드합니다.
    
    Returns:
        검토 로그 리스트
    """
    if REVIEW_LOG_FILE.exists():
        with open(REVIEW_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_review_log(logs: list) -> bool:
    """
    검토 로그를 저장합니다.
    
    Args:
        logs: 검토 로그 리스트
    
    Returns:
        저장 성공 여부
    """
    try:
        REVIEW_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEW_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"검토 로그 저장 실패: {e}")
        return False

def add_review_log(action: str, filename: str, post_title: str, feedback: str = "") -> bool:
    """
    검토 로그에 항목을 추가합니다.
    
    Args:
        action: 수행된 액션 (approved, rejected, regenerated, skipped, deleted)
        filename: 파일명
        post_title: 포스트 제목
        feedback: 피드백 (재생성 시)
    
    Returns:
        저장 성공 여부
    """
    logs = load_review_log()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "filename": filename,
        "post_title": post_title,
        "feedback": feedback
    }
    
    logs.append(log_entry)
    return save_review_log(logs)

# ==============================================================================
# 포스트 정보 추출
# ==============================================================================
def get_post_info(filename: str) -> dict:
    """
    포스트 파일에서 정보를 추출합니다.
    
    Args:
        filename: 파일명
    
    Returns:
        포스트 정보 딕셔너리
    """
    try:
        post_data = load_output_json(filename)
        return {
            "filename": filename,
            "title": post_data.get("title", "N/A"),
            "keyword": post_data.get("keyword", "N/A"),
            "category": post_data.get("category", "N/A"),
            "estimated_read_time": post_data.get("estimated_read_time", "N/A"),
            "seo_score": post_data.get("seo_score", "N/A"),
            "generated_at": post_data.get("generated_at", "N/A"),
            "content": post_data.get("content", ""),
            "meta_description": post_data.get("meta_description", ""),
            "tags": post_data.get("tags", []),
            "affiliate_opportunities": post_data.get("affiliate_opportunities", [])
        }
    except Exception as e:
        logger.error(f"포스트 정보 로드 실패: {e}")
        return None

# ==============================================================================
# 터미널 UI
# ==============================================================================
def clear_screen():
    """화면을 지웁니다."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_post_preview(post_info: dict):
    """
    포스트 미리보기를 출력합니다.
    
    Args:
        post_info: 포스트 정보
    """
    print(f"\n{'='*70}")
    print(f"📄 제목: {post_info['title']}")
    print(f"{'='*70}")
    print(f"🔑 키워드: {post_info['keyword']}")
    print(f"📁 카테고리: {post_info['category']}")
    print(f"⏱️ 예상 읽기 시간: {post_info['estimated_read_time']}분")
    print(f"📊 SEO 점수: {post_info['seo_score']}/100")
    print(f"🏷️ 태그: {', '.join(post_info['tags'])}")
    print(f"🔗 제휴 기회: {', '.join(post_info['affiliate_opportunities'])}")
    print(f"{'='*70}")
    
    # 본문 미리보기 (첫 500자)
    content = post_info['content']
    if len(content) > 500:
        preview = content[:500] + "..."
    else:
        preview = content
    
    print(f"\n📝 본문 미리보기:")
    print(f"{'-'*70}")
    print(preview)
    print(f"{'-'*70}")

def print_queue_list(posts: list):
    """
    대기열 목록을 출력합니다.
    
    Args:
        posts: 포스트 정보 리스트
    """
    print(f"\n{'='*70}")
    print(f"📋 검토 대기열 ({len(posts)}개 포스트)")
    print(f"{'='*70}")
    
    for i, post in enumerate(posts, 1):
        seo_score = post.get('seo_score', 'N/A')
        if isinstance(seo_score, (int, float)):
            seo_display = f"{seo_score}/100"
        else:
            seo_display = str(seo_score)
        
        print(f"{i}. {post['title'][:50]}...")
        print(f"   키워드: {post['keyword']} | 카테고리: {post['category']} | SEO: {seo_display}")
        print(f"   파일: {post['filename']}")
        print()

def get_user_choice(max_choice: int) -> str:
    """
    사용자 선택을 입력받습니다.
    
    Args:
        max_choice: 최대 선택 번호
    
    Returns:
        선택된 액션
    """
    while True:
        print(f"\n작업을 선택하세요:")
        print(f"  [A] 이 포스트 승인 → WordPress 발행")
        print(f"  [E] 편집 후 발행 (파일 열기)")
        print(f"  [R] 재생성 요청 (피드백 입력)")
        print(f"  [S] 건너뛰기 (나중에 검토)")
        print(f"  [D] 삭제")
        print(f"  [Q] 종료")
        print()
        
        choice = input("선택: ").strip().upper()
        
        if choice in ['A', 'E', 'R', 'S', 'D', 'Q']:
            return choice
        else:
            print("올바른 선택이 아닙니다. 다시 입력해주세요.")

def get_feedback() -> str:
    """
    재생성 피드백을 입력받습니다.
    
    Returns:
        피드백 문자열
    """
    print("\n재생성 피드백을 입력하세요 (엔터만 누르면 기본 피드백 사용):")
    print("예: 더 구체적인 예시 추가, 문장 길이 줄이기, 더 친근한 톤으로")
    feedback = input("피드백: ").strip()
    return feedback if feedback else "Improve content quality, add more specific examples, make it more engaging."

# ==============================================================================
# 메인 검토 루프
# ==============================================================================
def run_review_queue():
    """검토 대기열 메인 루프"""
    clear_screen()
    print("🔍 AI 블로그 포스트 검토 노드")
    print("="*70)
    
    # 대기열 파일 목록 가져오기
    files = list_output_files()
    
    # 이미 검토된 파일 필터링 (원본만 표시)
    review_logs = load_review_log()
    reviewed_files = {log['filename'] for log in review_logs}
    
    pending_files = [f for f in files if f not in reviewed_files or f.endswith('_optimized.json')]
    
    if not pending_files:
        print("\n✅ 검토할 포스트가 없습니다.")
        print("   먼저 'python scripts/generate_post.py --random'으로 포스트를 생성해주세요.")
        return
    
    # 최적화된 파일이 있으면 원본보다 먼저 표시
    def sort_key(f):
        if '_optimized' in f:
            return f.replace('_optimized', '_')
        return f
    
    pending_files.sort(key=sort_key)
    
    current_index = 0
    
    while current_index < len(pending_files):
        filename = pending_files[current_index]
        post_info = get_post_info(filename)
        
        if not post_info:
            current_index += 1
            continue
        
        clear_screen()
        print(f"\n📋 [{current_index + 1}/{len(pending_files)}] 포스트 검토")
        print_queue_list([post_info])
        print_post_preview(post_info)
        
        choice = get_user_choice(len(pending_files))
        
        if choice == 'Q':
            print("\n👋 검토를 종료합니다.")
            break
        
        elif choice == 'A':
            # 승인 → WordPress 발행
            print(f"\n✅ 포스트를 승인했습니다: {post_info['title']}")
            add_review_log("approved", filename, post_info['title'])
            
            # wp_publisher.py 실행
            try:
                from scripts.wp_publisher import publish_post
                result = publish_post(filename)
                if result:
                    print(f"📤 WordPress에 발행 완료!")
                else:
                    print(f"⚠️ WordPress 발행에 문제가 있습니다. 로그를 확인하세요.")
            except Exception as e:
                print(f"⚠️ WordPress 발행 중 오류: {e}")
            
            input("\n엔터를 누르면 다음 포스트로 이동합니다...")
            current_index += 1
        
        elif choice == 'E':
            # 편집 후 발행
            print(f"\n📝 편집 모드로 이동합니다...")
            print(f"   파일 경로: {ROOT_DIR / 'output' / filename}")
            print(f"   파일을 편집한 후 저장하고 엔터를 누르세요.")
            
            # 기본 편집기 열기
            editor = os.getenv('EDITOR', 'nano')
            os.system(f"{editor} {ROOT_DIR / 'output' / filename}")
            
            add_review_log("edited", filename, post_info['title'])
            print("편집 완료. 이 포스트를 발행하시겠습니까?")
            
            confirm = input("발행하시겠습니까? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    from scripts.wp_publisher import publish_post
                    publish_post(filename)
                except Exception as e:
                    print(f"⚠️ WordPress 발행 중 오류: {e}")
            
            current_index += 1
        
        elif choice == 'R':
            # 재생성 요청
            feedback = get_feedback()
            print(f"\n🔄 재생성 요청을 기록합니다...")
            print(f"   피드백: {feedback}")
            
            add_review_log("regenerated", filename, post_info['title'], feedback)
            
            # TODO: 실제 재생성 로직 연동
            print("⚠️ 재생성 기능은 현재 준비 중입니다.")
            print("   generate_post.py를 다시 실행하여 새 포스트를 생성해주세요.")
            
            input("\n엔터를 누르면 다음 포스트로 이동합니다...")
            current_index += 1
        
        elif choice == 'S':
            # 건너뛰기
            print(f"\n⏭️ 이 포스트를 건너뜁니다.")
            add_review_log("skipped", filename, post_info['title'])
            current_index += 1
        
        elif choice == 'D':
            # 삭제
            confirm = input("정말 삭제하시겠습니까? (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    os.remove(ROOT_DIR / 'output' / filename)
                    print(f"🗑️ 파일을 삭제했습니다: {filename}")
                    add_review_log("deleted", filename, post_info['title'])
                    # 목록에서 제거
                    pending_files.pop(current_index)
                    # 인덱스 조정 안 함 (다음 항목이 같은 인덱스에 옴)
                except Exception as e:
                    print(f"⚠️ 삭제 실패: {e}")
            else:
                print("삭제가 취소되었습니다.")

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="생성된 포스트를 검토하고 승인/거부/재생성 처리합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/review_queue.py          # 터미널 UI로 검토
  python scripts/review_queue.py --web    # 웹 UI로 검토
        """
    )
    
    parser.add_argument("--web", "-w", action="store_true", help="웹 UI 모드로 실행")
    
    args = parser.parse_args()
    
    # 환경변수 로드
    load_environment()
    
    if args.web:
        # 웹 UI 모드
        print("🌐 웹 UI를 시작합니다...")
        print("   http://localhost:5000 으로 접속하세요.")
        print("   종료하려면 Ctrl+C를 누르세요.")
        
        # Flask 앱 실행
        try:
            from web_review.app import app
            app.run(host='0.0.0.0', port=5000, debug=True)
        except ImportError:
            print("⚠️ 웹 UI를 실행할 수 없습니다. web_review/app.py를 확인해주세요.")
            print("   터미널 모드로 실행합니다...")
            run_review_queue()
    else:
        # 터미널 UI 모드
        run_review_queue()

if __name__ == "__main__":
    main()