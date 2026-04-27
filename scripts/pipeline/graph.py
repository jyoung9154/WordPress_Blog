# ==============================================================================
# LangGraph 파이프라인 그래프 정의
# ==============================================================================
# 이 파일의 역할: LangGraph 기반 파이프라인 그래프 구성 및 실행
# ==============================================================================

import sys
import os
from pathlib import Path
from typing import Dict, Any, TypedDict, Literal
from datetime import datetime

# LangGraph 임포트
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[WARNING] LangGraph가 설치되지 않았습니다. pip install langgraph 필요")

# 공통 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.common import (
    load_environment,
    setup_logging,
    save_json,
    ROOT_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("pipeline_graph", "pipeline_graph.log")

# ==============================================================================
# PipelineState 정의
# ==============================================================================
class PipelineState(TypedDict, total=False):
    """
    파이프라인 전체 상태를 관리하는 TypedDict
    각 노드에서 이 상태를 읽고 업데이트함
    """
    # 입력
    main_keyword: str
    
    # 노드 1: 서브카테고리 생성 결과
    subcategories: list
    subcategories_generated_at: str
    node_1_status: str
    
    # 노드 2: 키워드 생성 결과
    keywords: list
    keywords_generated_at: str
    node_2_status: str
    
    # 노드 3: 블로그 글 작성 결과
    generated_posts: list
    posts_generated_at: str
    node_3_status: str
    
    # 노드 4: SEO 최적화 결과
    optimized_posts: list
    seo_optimized_at: str
    node_4_status: str
    
    # 노드 5: 흥미도 체크 결과
    engagement_scores: list
    engagement_checked_at: str
    node_5_status: str
    
    # 노드 6: 검토 결과
    review_results: list
    review_completed_at: str
    node_6_status: str
    
    # 노드 7: WordPress 발행 결과
    published_posts: list
    publishing_completed_at: str
    node_7_status: str
    
    # 공통
    config: dict
    error: str
    waiting_for_review: bool
    review_queue_updated_at: str

# ==============================================================================
# 그래프 생성 함수
# ==============================================================================
def create_pipeline_graph():
    """
    LangGraph 파이프라인 그래프를 생성합니다.
    
    Returns:
        StateGraph 인스턴스
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph가 설치되지 않았습니다.")
    
    # 노드 임포트
    from .nodes import (
        subcategory_generator,
        keyword_generator,
        blog_writer,
        seo_optimizer,
        engagement_checker,
        reviewer,
        wordpress_publisher,
        human_review
    )
    
    # 그래프 생성
    graph = StateGraph(PipelineState)
    
    # 노드 추가
    graph.add_node("subcategory_generator", subcategory_generator)
    graph.add_node("keyword_generator", keyword_generator)
    graph.add_node("blog_writer", blog_writer)
    graph.add_node("seo_optimizer", seo_optimizer)
    graph.add_node("engagement_checker", engagement_checker)
    graph.add_node("reviewer", reviewer)
    graph.add_node("human_review", human_review)
    graph.add_node("wordpress_publisher", wordpress_publisher)
    
    # 시작 노드 설정
    graph.set_entry_point("subcategory_generator")
    
    # 엣지 (순차 실행)
    graph.add_edge("subcategory_generator", "keyword_generator")
    graph.add_edge("keyword_generator", "blog_writer")
    graph.add_edge("blog_writer", "seo_optimizer")
    graph.add_edge("seo_optimizer", "engagement_checker")
    graph.add_edge("engagement_checker", "reviewer")
    
    # 조건부 엣지: 자동 발행 vs 수동 검토
    def route_after_review(state: Dict[str, Any]) -> str:
        """검토 후 경로 결정"""
        config = state.get("config", {})
        auto_approve = config.get("auto_approve", False)
        
        if auto_approve:
            return "auto_publish"
        else:
            return "manual_review"
    
    graph.add_conditional_edges(
        "reviewer",
        route_after_review,
        {
            "auto_publish": "wordpress_publisher",
            "manual_review": "human_review"
        }
    )
    
    # 인간 검토 후 WordPress 발행
    graph.add_edge("human_review", "wordpress_publisher")
    
    # 종료
    graph.add_edge("wordpress_publisher", END)
    
    return graph

# ==============================================================================
# 파이프라인 실행 함수
# ==============================================================================
def run_pipeline(main_keyword: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    파이프라인을 실행합니다.
    
    Args:
        main_keyword: 메인 키워드
        config: 실행 설정
    
    Returns:
        최종 상태
    """
    if not LANGGRAPH_AVAILABLE:
        return {"error": "LangGraph가 설치되지 않았습니다."}
    
    logger.info(f"파이프라인 실행 시작: {main_keyword}")
    
    # 설정 기본값
    if config is None:
        config = {}
    
    default_config = {
        "auto_approve": False,  # 자동 승인 여부
        "auto_approve_threshold": 60,  # 자동 승인 기준 점수
        "max_posts": 3,  # 최대 생성 포스트 수
        "target_audience": "global"  # 대상 청중
    }
    default_config.update(config)
    
    # 초기 상태
    initial_state = {
        "main_keyword": main_keyword,
        "config": default_config,
        "generated_at": datetime.now().isoformat()
    }
    
    try:
        # 그래프 생성 및 컴파일
        graph = create_pipeline_graph()
        compiled_graph = graph.compile()
        
        # 실행
        final_state = compiled_graph.invoke(initial_state)
        
        logger.info("파이프라인 실행 완료")
        
        # 결과 저장
        result_filename = f"pipeline_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_data = {
            "main_keyword": main_keyword,
            "config": default_config,
            "completed_at": datetime.now().isoformat(),
            "status": "success" if not final_state.get("error") else "failed",
            "subcategories_count": len(final_state.get("subcategories", [])),
            "keywords_count": len(final_state.get("keywords", [])),
            "posts_generated": len(final_state.get("generated_posts", [])),
            "posts_published": len(final_state.get("published_posts", [])),
            "final_state": final_state
        }
        
        save_json(result_data, result_filename)
        logger.info(f"결과 저장: output/{result_filename}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"파이프라인 실행 실패: {e}")
        return {"error": str(e)}

# ==============================================================================
# 간단한 실행 (LangGraph 없이)
# ==============================================================================
def run_pipeline_simple(main_keyword: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    LangGraph 없이 순차 실행 (단순화 버전)
    
    Args:
        main_keyword: 메인 키워드
        config: 실행 설정
    
    Returns:
        최종 상태
    """
    from .nodes import (
        subcategory_generator,
        keyword_generator,
        blog_writer,
        seo_optimizer,
        engagement_checker,
        reviewer,
        wordpress_publisher
    )
    
    logger.info(f"단순 파이프라인 실행: {main_keyword}")
    
    # 설정
    if config is None:
        config = {}
    
    # 상태 초기화
    state = {
        "main_keyword": main_keyword,
        "config": config,
        "generated_at": datetime.now().isoformat()
    }
    
    # 순차 실행
    nodes = [
        ("서브카테고리 생성", subcategory_generator),
        ("키워드 생성", keyword_generator),
        ("블로그 글 작성", blog_writer),
        ("SEO 최적화", seo_optimizer),
        ("흥미도 체크", engagement_checker),
        ("검토", reviewer),
    ]
    
    for node_name, node_func in nodes:
        logger.info(f"[파이프라인] {node_name} 실행 중...")
        state = node_func(state)
        
        if state.get("error"):
            logger.error(f"[파이프라인] {node_name} 실패: {state.get('error')}")
            break
        
        logger.info(f"[파이프라인] {node_name} 완료")
    
    # 자동 발행
    if not state.get("error") and config.get("auto_approve", False):
        logger.info("[파이프라인] WordPress 발행 실행...")
        state = wordpress_publisher(state)
    
    return state

# ==============================================================================
# 테스트 실행
# ==============================================================================
if __name__ == "__main__":
    # 환경 로드
    load_environment()
    
    # 간단한 테스트 실행
    result = run_pipeline_simple("AI investing tips", {"auto_approve": False})
    
    print("\n" + "="*60)
    print("파이프라인 실행 결과")
    print("="*60)
    print(f"서브카테고리: {len(result.get('subcategories', []))}개")
    print(f"키워드: {len(result.get('keywords', []))}개")
    print(f"생성된 글: {len(result.get('generated_posts', []))}개")
    print(f"발행된 글: {len(result.get('published_posts', []))}개")
    
    if result.get("error"):
        print(f"오류: {result.get('error')}")