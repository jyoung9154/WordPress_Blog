#!/usr/bin/env python3
# ==============================================================================
# Flask 웹 검토 UI 앱
# ==============================================================================
# 이 파일의 역할: 브라우저에서 포스트를 검토하고 승인/거부/재생성할 수 있는 웹 UI
# 사용법: python web_review/app.py
#        http://localhost:5000 으로 접속
# ==============================================================================

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

# scripts 폴더의 common.py를 임포트하기 위해 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.common import (
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
# Flask 앱 설정
# ==============================================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False

# 로거 설정
logger = setup_logging("web_review", "web_review.log")

# ==============================================================================
# 헬퍼 함수
# ==============================================================================
def get_pending_posts():
    """
    검토 대기 중인 포스트 목록을 가져옵니다.
    
    Returns:
        포스트 정보 리스트
    """
    files = list_output_files()
    
    # 이미 검토된 파일 필터링
    review_logs = load_review_log()
    reviewed_files = {log['filename'] for log in review_logs}
    
    pending_files = []
    for f in files:
        if f.endswith('_optimized.json') or f.endswith('_affiliate.json'):
            base = f.replace('_optimized', '').replace('_affiliate', '')
            if base not in reviewed_files:
                pending_files.append(f)
        elif f.endswith('.json') and '_published' not in f:
            if f not in reviewed_files:
                pending_files.append(f)
    
    posts = []
    for filename in pending_files:
        try:
            post_data = load_output_json(filename)
            posts.append({
                'filename': filename,
                'title': post_data.get('title', 'N/A'),
                'keyword': post_data.get('keyword', 'N/A'),
                'category': post_data.get('category', 'N/A'),
                'seo_score': post_data.get('seo_score', 'N/A'),
                'estimated_read_time': post_data.get('estimated_read_time', 'N/A'),
                'generated_at': post_data.get('generated_at', 'N/A')
            })
        except Exception as e:
            logger.error(f"포스트 로드 실패 {filename}: {e}")
    
    return posts

def load_review_log():
    """
    검토 로그를 로드합니다.
    """
    log_file = LOGS_DIR / "review_log.json"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_review_log(logs):
    """
    검토 로그를 저장합니다.
    """
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / "review_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"검토 로그 저장 실패: {e}")
        return False

def add_review_log(action, filename, post_title, feedback=""):
    """
    검토 로그에 항목을 추가합니다.
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
# 라우트
# ==============================================================================
@app.route('/')
def index():
    """
    메인 페이지 - 검토 대기열 목록
    """
    posts = get_pending_posts()
    return render_template('index.html', posts=posts)

@app.route('/post/<path:filename>')
def view_post(filename):
    """
    포스트 상세 보기
    """
    try:
        post_data = load_output_json(filename)
        return render_template('post.html', post=post_data, filename=filename)
    except Exception as e:
        logger.error(f"포스트 로드 실패: {e}")
        return f"포스트를 로드할 수 없습니다: {e}", 404

@app.route('/preview/<path:filename>')
def preview_post(filename):
    """
    포스트 미리보기 (JSON 데이터)
    """
    try:
        post_data = load_output_json(filename)
        return jsonify(post_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/approve', methods=['POST'])
def approve_post():
    """
    포스트 승인 → WordPress 발행
    """
    data = request.get_json()
    filename = data.get('filename')
    post_title = data.get('title', 'N/A')
    
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400
    
    # 검토 로그에 추가
    add_review_log("approved", filename, post_title)
    
    # WordPress 발행 시도
    try:
        from scripts.wp_publisher import publish_post
        result = publish_post(filename)
        
        if result:
            return jsonify({
                "success": True, 
                "message": "WordPress에 발행되었습니다!",
                "url": result.get('url', '')
            })
        else:
            return jsonify({
                "success": True, 
                "message": "승인 완료. WordPress 발행은 나중에 처리됩니다."
            })
    except Exception as e:
        logger.error(f"WordPress 발행 실패: {e}")
        return jsonify({
            "success": True, 
            "message": f"승인 완료. WordPress 발행 중 오류: {str(e)}"
        })

@app.route('/reject', methods=['POST'])
def reject_post():
    """
    포스트 거부
    """
    data = request.get_json()
    filename = data.get('filename')
    post_title = data.get('title', 'N/A')
    reason = data.get('reason', '')
    
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400
    
    add_review_log("rejected", filename, post_title, reason)
    
    return jsonify({"success": True, "message": "포스트가 거부되었습니다."})

@app.route('/regenerate', methods=['POST'])
def regenerate_post():
    """
    포스트 재생성 요청
    """
    data = request.get_json()
    filename = data.get('filename')
    post_title = data.get('title', 'N/A')
    feedback = data.get('feedback', '')
    
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400
    
    add_review_log("regenerated", filename, post_title, feedback)
    
    return jsonify({
        "success": True, 
        "message": "재생성 요청이 기록되었습니다. 새 포스트를 생성해주세요."
    })

@app.route('/skip', methods=['POST'])
def skip_post():
    """
    포스트 건너뛰기
    """
    data = request.get_json()
    filename = data.get('filename')
    post_title = data.get('title', 'N/A')
    
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400
    
    add_review_log("skipped", filename, post_title)
    
    return jsonify({"success": True, "message": "포스트가 건너뛰어졌습니다."})

@app.route('/delete', methods=['POST'])
def delete_post():
    """
    포스트 삭제
    """
    data = request.get_json()
    filename = data.get('filename')
    post_title = data.get('title', 'N/A')
    
    if not filename:
        return jsonify({"success": False, "error": "filename is required"}), 400
    
    try:
        # 파일 삭제
        file_path = ROOT_DIR / "output" / filename
        if file_path.exists():
            file_path.unlink()
        
        add_review_log("deleted", filename, post_title)
        
        return jsonify({"success": True, "message": "포스트가 삭제되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logs')
def view_logs():
    """
    검토 로그 보기
    """
    logs = load_review_log()
    return render_template('logs.html', logs=logs)

@app.route('/stats')
def stats():
    """
    통계 대시보드
    """
    logs = load_review_log()
    posts = get_pending_posts()
    
    # 통계 계산
    total_reviews = len(logs)
    approved = sum(1 for log in logs if log['action'] == 'approved')
    rejected = sum(1 for log in logs if log['action'] == 'rejected')
    skipped = sum(1 for log in logs if log['action'] == 'skipped')
    deleted = sum(1 for log in logs if log['action'] == 'deleted')
    
    # 월간 통계
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    monthly_logs = [
        log for log in logs 
        if datetime.fromisoformat(log["timestamp"]) >= month_start
    ]
    monthly_approved = sum(1 for log in monthly_logs if log['action'] == 'approved')
    
    return jsonify({
        "total_reviews": total_reviews,
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
        "deleted": deleted,
        "pending": len(posts),
        "monthly_approved": monthly_approved,
        "success_rate": round(approved / total_reviews * 100, 1) if total_reviews > 0 else 0
    })

# ==============================================================================
# 에러 핸들러
# ==============================================================================
@app.errorhandler(404)
def not_found(e):
    """404 에러 페이지"""
    return render_template('error.html', error="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def server_error(e):
    """500 에러 페이지"""
    return render_template('error.html', error="서버 오류가 발생했습니다."), 500

# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == "__main__":
    # 환경변수 로드
    load_environment()
    
    print("="*60)
    print("🌐 AI 블로그 검토 웹 UI")
    print("="*60)
    print("접속 주소: http://localhost:5000")
    print("종료하려면 Ctrl+C를 누르세요")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)