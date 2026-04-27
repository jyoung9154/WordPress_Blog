# ==============================================================================
# LangGraph 파이프라인 패키지
# ==============================================================================
# 이 파일의 역할: LangGraph 기반 파이프라인 노드 및 그래프 정의
# 
# 노드 구성:
# 1. subcategory_generator - 메인키워드 → 서브카테고리 생성
# 2. keyword_generator - 서브카테고리 → 키워드 생성
# 3. blog_writer - 키워드 → 블로그 글 작성 (MCP 연동 가능)
# 4. seo_optimizer - 글 → SEO 최적화
# 5. engagement_checker - 글 → 흥미도/참여도 체크
# 6. reviewer - 최종 검토 후 WordPress 발행
# ==============================================================================

from .nodes import (
    subcategory_generator,
    keyword_generator,
    blog_writer,
    seo_optimizer,
    engagement_checker,
    reviewer,
    human_review
)

from .graph import (
    create_pipeline_graph,
    PipelineState,
    run_pipeline
)

__all__ = [
    'subcategory_generator',
    'keyword_generator', 
    'blog_writer',
    'seo_optimizer',
    'engagement_checker',
    'reviewer',
    'human_review',
    'create_pipeline_graph',
    'PipelineState',
    'run_pipeline'
]