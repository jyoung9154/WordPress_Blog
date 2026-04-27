#!/usr/bin/env python3
# ==============================================================================
# 관리 대시보드 앱
# ==============================================================================
# 이 파일의 역할: CLI/웹으로 설정 관리, WordPress 관리, AI 프로바이더 선택, 모니터링
# 사용법: python web_review/admin.py
#        http://localhost:5001 으로 접속
# ==============================================================================

import os
import sys
import json
import argparse
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
    get_ai_client,
    ROOT_DIR,
    LOGS_DIR,
    CONFIG_DIR
)

# ==============================================================================
# Flask 앱 설정
# ==============================================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'admin-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False

# 로거 설정
logger = setup_logging("admin_dashboard", "admin_dashboard.log")

# ==============================================================================
# 헬퍼 함수
# ==============================================================================
def get_all_stats():
    """전체 통계 데이터 수집"""
    stats = {
        "posts": {},
        "ai_providers": {},
        "categories": {},
        "scheduler": {}
    }
    
    # 포스트 통계
    output_files = list_output_files()
    stats["posts"]["total"] = len(output_files)
    stats["posts"]["pending"] = len([f for f in output_files if '_published' not in f])
    stats["posts"]["published"] = len([f for f in output_files if '_published' in f])
    
    # AI 프로바이더 상태
    try:
        ai_client = get_ai_client()
        providers = ai_client.get_available_providers()
        stats["ai_providers"]["available"] = providers
        stats["ai_providers"]["current"] = ai_client.current_provider
    except Exception as e:
        stats["ai_providers"]["error"] = str(e)
    
    # 카테고리 통계
    try:
        topics = load_json("topics.json")
        stats["categories"]["total"] = len(topics.get("categories", []))
        stats["categories"]["main"] = len(topics.get("main_categories", []))
    except Exception as e:
        stats["categories"]["error"] = str(e)
    
    # 스케줄러 상태
    try:
        status_file = LOGS_DIR / "scheduler_status.json"
        if status_file.exists():
            with open(status_file, 'r') as f:
                stats["scheduler"] = json.load(f)
    except Exception as e:
        stats["scheduler"]["error"] = str(e)
    
    return stats

def get_env_config():
    """환경변수 설정값 읽기"""
    config = {}
    env_file = ROOT_DIR / ".env"
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 민감한 정보 마스킹
                    if any(s in key.lower() for s in ['password', 'key', 'secret', 'token']):
                        if value:
                            value = '*' * 8 + value[-4:] if len(value) > 4 else '****'
                    config[key] = value
    
    return config

def save_env_config(config: dict):
    """환경변수 설정값 저장"""
    env_file = ROOT_DIR / ".env"
    
    # 기존 파일 읽기
    existing = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing[key] = value
    
    # 새 값으로 업데이트
    existing.update(config)
    
    # 파일 쓰기
    with open(env_file, 'w') as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")
    
    return True

# ==============================================================================
# 라우트 - 메인 대시보드
# ==============================================================================
@app.route('/')
def index():
    """메인 대시보드"""
    stats = get_all_stats()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/settings')
def settings():
    """설정 페이지"""
    env_config = get_env_config()
    return render_template('admin/settings.html', config=env_config)

@app.route('/settings/ai', methods=['GET', 'POST'])
def settings_ai():
    """AI 프로바이더 설정"""
    if request.method == 'POST':
        data = request.get_json()
        
        # AI 프로바이더 설정 저장
        config = {
            'AI_PROVIDER': data.get('provider', 'claude')
        }
        
        # 선택된 프로바이더의 API 키가 있으면 추가
        provider = data.get('provider', 'claude')
        if provider == 'claude' and data.get('claude_api_key'):
            config['CLAUDE_API_KEY'] = data.get('claude_api_key')
        elif provider == 'openai' and data.get('openai_api_key'):
            config['OPENAI_API_KEY'] = data.get('openai_api_key')
        elif provider == 'gemini' and data.get('gemini_api_key'):
            config['GEMINI_API_KEY'] = data.get('gemini_api_key')
        elif provider == 'groq' and data.get('groq_api_key'):
            config['GROQ_API_KEY'] = data.get('groq_api_key')
        
        save_env_config(config)
        
        return jsonify({"success": True, "message": "AI 설정이 저장되었습니다."})
    
    # GET 요청
    env_config = get_env_config()
    try:
        ai_client = get_ai_client()
        available = ai_client.get_available_providers()
        current = ai_client.current_provider
    except:
        available = []
        current = 'claude'
    
    return render_template('admin/settings_ai.html', 
                         available_providers=available,
                         current_provider=current,
                         config=env_config)

@app.route('/settings/wordpress', methods=['GET', 'POST'])
def settings_wordpress():
    """WordPress 설정"""
    if request.method == 'POST':
        data = request.get_json()
        
        config = {
            'WP_SITE_URL': data.get('site_url', ''),
            'WP_API_USERNAME': data.get('username', ''),
            'WP_API_PASSWORD': data.get('password', '')
        }
        
        save_env_config(config)
        
        return jsonify({"success": True, "message": "WordPress 설정이 저장되었습니다."})
    
    env_config = get_env_config()
    return render_template('admin/settings_wordpress.html', config=env_config)

@app.route('/settings/categories')
def settings_categories():
    """카테고리/키워드 관리"""
    try:
        topics = load_json("topics.json")
        return render_template('admin/settings_categories.html', 
                             topics=topics,
                             main_categories=topics.get("main_categories", []),
                             categories=topics.get("categories", []))
    except Exception as e:
        return f"설정 로드 오류: {e}", 500

@app.route('/settings/categories/save', methods=['POST'])
def save_categories():
    """카테고리 저장"""
    data = request.get_json()
    
    try:
        save_json(data, "topics.json")
        return jsonify({"success": True, "message": "카테고리가 저장되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/monitoring')
def monitoring():
    """모니터링 대시보드"""
    stats = get_all_stats()
    
    # 로그 파일 읽기
    logs = []
    log_files = ['generate_post.log', 'seo_optimizer.log', 'wp_publisher.log', 'scheduler.log']
    
    for log_file in log_files:
        log_path = LOGS_DIR / log_file
        if log_path.exists():
            with open(log_path, 'r') as f:
                lines = f.readlines()
                # 마지막 50줄만
                logs.extend([(log_file, line.strip()) for line in lines[-50:]])
    
    # 최신 로그 먼저
    logs.reverse()
    
    return render_template('admin/monitoring.html', stats=stats, logs=logs[:100])

@app.route('/posts')
def posts_list():
    """포스트 목록"""
    files = list_output_files()
    posts = []
    
    for f in files:
        try:
            data = load_output_json(f)
            posts.append({
                'filename': f,
                'title': data.get('title', 'N/A'),
                'keyword': data.get('keyword', 'N/A'),
                'category': data.get('category', 'N/A'),
                'status': 'published' if '_published' in f else 'draft',
                'seo_score': data.get('seo_score', 'N/A'),
                'generated_at': data.get('generated_at', 'N/A')
            })
        except:
            posts.append({
                'filename': f,
                'title': 'Error loading',
                'status': 'error'
            })
    
    return render_template('admin/posts.html', posts=posts)

@app.route('/api/stats')
def api_stats():
    """통계 API"""
    return jsonify(get_all_stats())

@app.route('/api/test-ai', methods=['POST'])
def test_ai():
    """AI 연결 테스트"""
    data = request.get_json()
    provider = data.get('provider', 'claude')
    
    try:
        ai_client = get_ai_client()
        ai_client.set_provider(provider)
        
        # 간단한 테스트 프롬프트
        result = ai_client.generate(
            prompt="Say 'AI connection successful!' in exactly those words.",
            max_tokens=50
        )
        
        return jsonify({"success": True, "message": "AI 연결 성공!", "response": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/test-wordpress', methods=['POST'])
def test_wordpress():
    """WordPress 연결 테스트"""
    from scripts.wp_publisher import WordPressPublisher
    from scripts.common import get_wordpress_config
    
    try:
        wp_config = get_wordpress_config()
        publisher = WordPressPublisher(
            site_url=wp_config['site_url'],
            username=wp_config['username'],
            password=wp_config['password']
        )
        
        if publisher.check_connection():
            return jsonify({"success": True, "message": "WordPress 연결 성공!"})
        else:
            return jsonify({"success": False, "error": "연결 실패"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==============================================================================
# CLI 모드
# ==============================================================================
def run_cli_mode():
    """CLI 관리 모드"""
    print("\n" + "="*60)
    print("🤖 AI 블로그 관리 시스템 - CLI 모드")
    print("="*60)
    
    while True:
        print("\n메뉴를 선택하세요:")
        print("  [1] 대시보드 보기 (통계)")
        print("  [2] AI 프로바이더 설정")
        print("  [3] WordPress 설정")
        print("  [4] 카테고리/키워드 관리")
        print("  [5] 모니터링 (로그)")
        print("  [6] 포스트 목록")
        print("  [7] 환경설정 파일 편집")
        print("  [0] 종료")
        
        choice = input("\n선택: ").strip()
        
        if choice == '1':
            stats = get_all_stats()
            print("\n" + "="*40)
            print("📊 대시보드 통계")
            print("="*40)
            print(f"총 포스트: {stats['posts']['total']}")
            print(f"  - 대기 중: {stats['posts']['pending']}")
            print(f"  - 발행됨: {stats['posts']['published']}")
            print(f"\nAI 프로바이더:")
            print(f"  - 현재: {stats['ai_providers'].get('current', 'N/A')}")
            print(f"  - 사용 가능: {', '.join(stats['ai_providers'].get('available', []))}")
            print(f"\n카테고리: {stats['categories'].get('total', 0)}개")
            print(f"메인 카테고리: {stats['categories'].get('main', 0)}개")
        
        elif choice == '2':
            print("\n--- AI 프로바이더 설정 ---")
            try:
                ai_client = get_ai_client()
                available = ai_client.get_available_providers()
                print(f"사용 가능한 프로바이더: {', '.join(available) if available else '없음'}")
                print(f"현재 프로바이더: {ai_client.current_provider}")
            except Exception as e:
                print(f"오류: {e}")
            
            print("\n프로바이더를 변경하려면 .env 파일을 편집하세요:")
            print("  AI_PROVIDER=claude  # 또는 openai, gemini, groq, ollama")
        
        elif choice == '3':
            print("\n--- WordPress 설정 ---")
            env_config = get_env_config()
            print(f"SITE URL: {env_config.get('WP_SITE_URL', 'N/A')}")
            print(f"USERNAME: {env_config.get('WP_API_USERNAME', 'N/A')}")
            print(f"PASSWORD: {'*' * 8}")
            
            print("\nWordPress 설정을 변경하려면 .env 파일을 편집하세요.")
        
        elif choice == '4':
            print("\n--- 카테고리/키워드 관리 ---")
            try:
                topics = load_json("topics.json")
                print(f"\n메인 카테고리 ({len(topics.get('main_categories', []))}개):")
                for cat in topics.get("main_categories", []):
                    print(f"  {cat.get('icon', '')} {cat.get('name', '')}")
                
                print(f"\n서브 카테고리 ({len(topics.get('categories', []))}개):")
                for cat in topics.get("categories", []):
                    print(f"  - {cat.get('name', '')} ({cat.get('main_category', '')})")
            except Exception as e:
                print(f"오류: {e}")
            
            print("\n카테고리를 편집하려면 config/topics.json 파일을 편집하세요.")
        
        elif choice == '5':
            print("\n--- 모니터링 ---")
            stats = get_all_stats()
            scheduler = stats.get('scheduler', {})
            print(f"스케줄러 상태: {'🟢 실행 중' if scheduler.get('running') else '🔴 중지됨'}")
            print(f"총 실행: {scheduler.get('total_runs', 0)}")
            print(f"성공: {scheduler.get('successful_runs', 0)}")
            print(f"실패: {scheduler.get('failed_runs', 0)}")
            
            if scheduler.get('last_run'):
                print(f"마지막 실행: {scheduler.get('last_run')}")
        
        elif choice == '6':
            print("\n--- 포스트 목록 ---")
            files = list_output_files()
            print(f"총 {len(files)}개 파일")
            
            for f in files[:10]:  # 처음 10개만
                status = "✅" if "_published" in f else "📝"
                print(f"  {status} {f}")
            
            if len(files) > 10:
                print(f"  ... 외 {len(files) - 10}개")
        
        elif choice == '7':
            print("\n--- 환경설정 편집 ---")
            editor = os.getenv('EDITOR', 'nano')
            os.system(f"{editor} {ROOT_DIR / '.env'}")
        
        elif choice == '0':
            print("\n안녕히 가세요!")
            break
        
        else:
            print("올바른 선택이 아닙니다.")

# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == "__main__":
    # 환경변수 로드
    load_environment()
    
    parser = argparse.ArgumentParser(description="AI 블로그 관리 대시보드")
    parser.add_argument("--cli", "-c", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--port", "-p", type=int, default=5001, help="웹 서버 포트 (기본: 5001)")
    
    args = parser.parse_args()
    
    if args.cli:
        run_cli_mode()
    else:
        print("="*60)
        print("🌐 AI 블로그 관리 대시보드")
        print("="*60)
        print(f"접속 주소: http://localhost:{args.port}")
        print(f"CLI 모드: python web_review/admin.py --cli")
        print("종료하려면 Ctrl+C를 누르세요")
        print("="*60)
        
        app.run(host='0.0.0.0', port=args.port, debug=True)