#!/usr/bin/env python3
# ==============================================================================
# LangGraph 파이프라인 노드 에디터 (n8n 스타일)
# ==============================================================================
# 이 파일의 역할: 드래그 앤 드롭으로 LangGraph 노드 구성, 저장, 실행
# 사용법: python web_review/pipeline_editor.py
# http://localhost:5002 으로 접속
# ==============================================================================

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.common import (
    load_environment,
    setup_logging,
    load_json,
    save_json,
    ROOT_DIR,
    CONFIG_DIR,
    LOGS_DIR
)

# ==============================================================================
# Flask 앱 설정
# ==============================================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'pipeline-editor-secret-key')
app.config['JSON_AS_ASCII'] = False

logger = setup_logging("pipeline_editor", "pipeline_editor.log")

# ==============================================================================
# 기본 노드 정의
# ==============================================================================
DEFAULT_NODES = [
    {
        "id": "node_1",
        "type": "subcategory_generator",
        "name": "서브카테고리 생성",
        "icon": "📂",
        "description": "메인키워드 → 서브카테고리 생성",
        "color": "#667eea",
        "inputs": ["main_keyword"],
        "outputs": ["subcategories"],
        "config": {
            "max_subcategories": 5,
            "ai_provider": "claude"
        }
    },
    {
        "id": "node_2",
        "type": "keyword_generator",
        "name": "키워드 생성",
        "icon": "🔑",
        "description": "서브카테고리 → 키워드 생성",
        "color": "#4caf50",
        "inputs": ["subcategories"],
        "outputs": ["keywords"],
        "config": {
            "keywords_per_subcategory": 5,
            "include_long_tail": True
        }
    },
    {
        "id": "node_3",
        "type": "blog_writer",
        "name": "블로그 글 작성",
        "icon": "✍️",
        "description": "키워드 → 블로그 글 작성 (MCP 연동)",
        "color": "#ff9800",
        "inputs": ["keywords"],
        "outputs": ["generated_posts"],
        "config": {
            "max_posts": 3,
            "min_word_count": 1500,
            "style": "professional"
        }
    },
    {
        "id": "node_4",
        "type": "seo_optimizer",
        "name": "SEO 최적화",
        "icon": "🔍",
        "description": "글 → SEO 최적화 처리",
        "color": "#9c27b0",
        "inputs": ["generated_posts"],
        "outputs": ["optimized_posts"],
        "config": {
            "target_keyword_density": 2.0,
            "min_seo_score": 70
        }
    },
    {
        "id": "node_5",
        "type": "engagement_checker",
        "name": "흥미도 체크",
        "icon": "📊",
        "description": "글 → 흥미도/참여도 예측",
        "color": "#00bcd4",
        "inputs": ["optimized_posts"],
        "outputs": ["engagement_scores"],
        "config": {
            "engagement_threshold": 60
        }
    },
    {
        "id": "node_6",
        "type": "reviewer",
        "name": "검토 노드",
        "icon": "✅",
        "description": "최종 검토 및 승인/거부",
        "color": "#795548",
        "inputs": ["engagement_scores"],
        "outputs": ["review_results"],
        "config": {
            "auto_approve_threshold": 60,
            "require_human_review": True
        }
    },
    {
        "id": "node_7",
        "type": "wordpress_publisher",
        "name": "WordPress 발행",
        "icon": "🌐",
        "description": "승인된 글 → WordPress 발행",
        "color": "#607d8b",
        "inputs": ["review_results"],
        "outputs": ["published_posts"],
        "config": {
            "publish_status": "publish"
        }
    }
]

# ==============================================================================
# 기본 엣지 정의
# ==============================================================================
DEFAULT_EDGES = [
    {"from": "node_1", "to": "node_2", "label": "subcategories"},
    {"from": "node_2", "to": "node_3", "label": "keywords"},
    {"from": "node_3", "to": "node_4", "label": "generated_posts"},
    {"from": "node_4", "to": "node_5", "label": "optimized_posts"},
    {"from": "node_5", "to": "node_6", "label": "engagement_scores"},
    {"from": "node_6", "to": "node_7", "label": "review_results"}
]

# ==============================================================================
# 파이프라인 저장/로드
# ==============================================================================
def get_pipeline_path(name: str = "default") -> Path:
    """파이프라인 파일 경로 반환"""
    return CONFIG_DIR / f"pipeline_{name}.json"

def load_pipeline(name: str = "default") -> dict:
    """파이프라인 로드"""
    path = get_pipeline_path(name)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "name": name,
        "nodes": DEFAULT_NODES,
        "edges": DEFAULT_EDGES,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

def save_pipeline(pipeline_data: dict, name: str = "default") -> bool:
    """파이프라인 저장"""
    try:
        pipeline_data["updated_at"] = datetime.now().isoformat()
        path = get_pipeline_path(name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(pipeline_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"파이프라인 저장 실패: {e}")
        return False

def list_pipelines() -> list:
    """저장된 파이프라인 목록"""
    pipelines = []
    for f in CONFIG_DIR.glob("pipeline_*.json"):
        name = f.stem.replace("pipeline_", "")
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        pipelines.append({
            "name": name,
            "node_count": len(data.get("nodes", [])),
            "updated_at": data.get("updated_at", "")
        })
    return sorted(pipelines, key=lambda x: x["updated_at"], reverse=True)

# ==============================================================================
# 다익스트라 스타일 위상 정렬
# ==============================================================================
def topological_sort(nodes: list, edges: list) -> list:
    """다익스트라 스타일 위상 정렬 - 노드 실행 순서 계산"""
    graph = {node['id']: [] for node in nodes}
    in_degree = {node['id']: 0 for node in nodes}
    
    for edge in edges:
        from_node = edge.get('from')
        to_node = edge.get('to')
        if from_node in graph and to_node in graph:
            graph[from_node].append(to_node)
            in_degree[to_node] += 1

    queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        current_level = queue.copy()
        queue.clear()
        
        for node_id in current_level:
            result.append(node_id)
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    return result

# ==============================================================================
# SSE 이벤트 포맷 헬퍼
# ==============================================================================
def sse_event(event_name: str, data: dict) -> str:
    """SSE 이벤트 포맷 생성"""
    json_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event_name}\ndata: {json_str}\n\n"

# ==============================================================================
# 라우트
# ==============================================================================
@app.route('/')
def index():
    """파이프라인 에디터 메인 페이지"""
    pipeline = load_pipeline("default")
    pipelines = list_pipelines()
    return render_template('pipeline_editor/index.html',
                           pipeline=pipeline,
                           pipelines=pipelines,
                           default_nodes=DEFAULT_NODES)

@app.route('/api/pipeline', methods=['GET'])
def api_get_pipeline():
    """파이프라인 데이터 API"""
    name = request.args.get('name', 'default')
    pipeline = load_pipeline(name)
    return jsonify(pipeline)

@app.route('/api/pipeline', methods=['POST'])
def api_save_pipeline():
    """파이프라인 저장 API"""
    data = request.get_json()
    name = data.get('name', 'default')

    if save_pipeline(data, name):
        return jsonify({"success": True, "message": "파이프라인이 저장되었습니다."})
    else:
        return jsonify({"success": False, "error": "저장 실패"}), 500

@app.route('/api/pipeline/run', methods=['POST'])
def api_run_pipeline():
    """파이프라인 실행 API"""
    data = request.get_json()
    main_keyword = data.get('main_keyword', '')
    config = data.get('config', {})

    if not main_keyword:
        return jsonify({"success": False, "error": "메인키워드가 필요합니다."}), 400

    try:
        from scripts.pipeline.graph import run_pipeline_simple
        result = run_pipeline_simple(main_keyword, config)

        return jsonify({
            "success": True,
            "message": "파이프라인 실행 완료",
            "result": {
                "subcategories_count": len(result.get('subcategories', [])),
                "keywords_count": len(result.get('keywords', [])),
                "posts_generated": len(result.get('generated_posts', [])),
                "posts_published": len(result.get('published_posts', [])),
                "error": result.get('error')
            }
        })
    except Exception as e:
        logger.error(f"파이프라인 실행 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pipeline/run-stream', methods=['POST'])
def api_run_pipeline_stream():
    """파이프라인 실행 API (SSE 실시간 진행 스트림 - 다익스트라 스타일)"""
    from flask import Response
    import time
    
    data = request.get_json()
    main_keyword = data.get('main_keyword', '')
    config = data.get('config', {})
    pipeline_nodes = data.get('nodes', DEFAULT_NODES)
    pipeline_edges = data.get('edges', DEFAULT_EDGES)

    if not main_keyword:
        return jsonify({"success": False, "error": "메인키워드가 필요합니다."}), 400

    def generate():
        """SSE 스트림 생성기 - 다익스트라 알고리즘 스타일 진행 표시"""
        try:
            # 1. 파이프라인 초기화 이벤트
            init_data = {
                'type': 'init',
                'message': '파이프라인 시작...',
                'main_keyword': main_keyword
            }
            yield sse_event('init', init_data)
            time.sleep(0.5)

            # 2. 노드 순서 계산 (다익스트라 스타일 위상 정렬)
            node_order = topological_sort(pipeline_nodes, pipeline_edges)
            order_data = {
                'type': 'node_order',
                'order': node_order,
                'total_nodes': len(node_order)
            }
            yield sse_event('node_order', order_data)
            time.sleep(0.3)

            # 3. 각 노드 순차 실행 (다익스트라 BFS 스타일)
            for i, node_id in enumerate(node_order):
                node = next((n for n in pipeline_nodes if n['id'] == node_id), None)
                if not node:
                    continue

                # 노드 시작 이벤트
                progress = int((i / len(node_order)) * 100)
                node_name = node.get('name', node_id)
                start_data = {
                    'type': 'node_start',
                    'node_id': node_id,
                    'node_name': node_name,
                    'node_type': node.get('type', ''),
                    'node_color': node.get('color', '#667eea'),
                    'progress': progress,
                    'message': f'{node_name} 시작...',
                    'step': i + 1,
                    'total_steps': len(node_order)
                }
                yield sse_event('node_start', start_data)

                # 시뮬레이션: 각 노드 실행 시간 (실제 실행 시 제거)
                time.sleep(1.5)

                # 노드 완료 이벤트
                complete_progress = int(((i + 1) / len(node_order)) * 100)
                output_count = len(node.get('outputs', []))
                complete_data = {
                    'type': 'node_complete',
                    'node_id': node_id,
                    'node_name': node_name,
                    'progress': complete_progress,
                    'message': f'{node_name} 완료!',
                    'output': f'{output_count}개 출력 생성',
                    'step': i + 1,
                    'total_steps': len(node_order)
                }
                yield sse_event('node_complete', complete_data)
                time.sleep(0.3)

            # 4. 전체 완료 이벤트
            complete_data = {
                'type': 'complete',
                'progress': 100,
                'message': '모든 노드 실행 완료!',
                'summary': {
                    'total_nodes': len(node_order),
                    'execution_time': '약 10초',
                    'main_keyword': main_keyword
                }
            }
            yield sse_event('complete', complete_data)

        except Exception as e:
            logger.error(f"SSE 파이프라인 실행 실패: {e}")
            error_data = {'type': 'error', 'message': str(e)}
            yield sse_event('error', error_data)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/nodes', methods=['GET'])
def api_get_nodes():
    """사용 가능한 노드 목록"""
    return jsonify(DEFAULT_NODES)

@app.route('/api/pipelines', methods=['GET'])
def api_list_pipelines():
    """저장된 파이프라인 목록"""
    return jsonify(list_pipelines())

# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == "__main__":
    load_environment()

    print("="*60)
    print("🔗 LangGraph 파이프라인 에디터 (n8n 스타일)")
    print("   - 다익스트라 스타일 실시간 진행 표시")
    print("="*60)
    print("접속 주소: http://localhost:5002")
    print("종료하려면 Ctrl+C를 누르세요")
    print("="*60)

    app.run(host='0.0.0.0', port=5002, debug=True)