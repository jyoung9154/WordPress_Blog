# ==============================================================================
# LangGraph 노드 정의
# ==============================================================================
# 이 파일의 역할: 각 파이프라인 노드의 로직 정의
# 각 노드는 PipelineState를 입력받아 상태를 업데이트하여 반환
# ==============================================================================

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 공통 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.common import (
    load_environment,
    setup_logging,
    load_json,
    get_ai_client,
    generate_timestamp,
    save_json
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("pipeline_nodes", "pipeline_nodes.log")

# ==============================================================================
# 노드 1: 서브카테고리 생성
# ==============================================================================
def subcategory_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    메인키워드를 기반으로 서브카테고리를 생성합니다.
    
    Args:
        state: 파이프라인 상태 (main_keyword 포함)
    
    Returns:
        업데이트된 상태 (subcategories 추가)
    """
    logger.info(f"[노드1] 서브카테고리 생성 시작: {state.get('main_keyword', '')}")
    
    main_keyword = state.get("main_keyword", "")
    if not main_keyword:
        state["error"] = "메인키워드가 없습니다"
        return state
    
    try:
        ai_client = get_ai_client()
        
        prompt = f"""Based on the main keyword "{main_keyword}", generate 3-5 relevant subcategories for a blog.

For each subcategory, provide:
1. name: Subcategory name in English
2. slug: URL-friendly slug
3. description: Brief description
4. priority: Priority level (1-5, 1 is highest)

Return the result as a JSON array with this structure:
[
  {{"name": "...", "slug": "...", "description": "...", "priority": 1}},
  ...
]

Consider these main categories:
- AI & Technology
- Finance & Investing  
- Economy & Markets
- AI Skills & Prompts

Return ONLY the JSON array, no additional text."""

        response = ai_client.generate(
            prompt=prompt,
            system_prompt="You are an expert blog content strategist. Return valid JSON only.",
            max_tokens=2000
        )
        
        # JSON 파싱
        import json
        # 마크다운 코드 블록 제거
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        subcategories = json.loads(response)
        
        state["subcategories"] = subcategories
        state["subcategories_generated_at"] = datetime.now().isoformat()
        state["node_1_status"] = "success"
        
        logger.info(f"[노드1] 서브카테고리 {len(subcategories)}개 생성 완료")
        
    except Exception as e:
        logger.error(f"[노드1] 서브카테고리 생성 실패: {e}")
        state["error"] = str(e)
        state["node_1_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 2: 키워드 생성
# ==============================================================================
def keyword_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    각 서브카테고리별로 키워드를 생성합니다.
    
    Args:
        state: 파이프라인 상태 (subcategories 포함)
    
    Returns:
        업데이트된 상태 (keywords 추가)
    """
    logger.info("[노드2] 키워드 생성 시작")
    
    subcategories = state.get("subcategories", [])
    if not subcategories:
        state["error"] = "서브카테고리가 없습니다"
        return state
    
    try:
        ai_client = get_ai_client()
        all_keywords = []
        
        for subcat in subcategories:
            prompt = f"""For the subcategory "{subcat['name']}" ({subcat['description']}), 
generate 5-8 keywords for blog posts.

Each keyword should be:
- Specific and searchable
- Include the main topic naturally
- Have good search volume potential

Return as a JSON array:
[
  {{"keyword": "...", "competition": "low/medium/high", "cpc_range": "$X-$Y", "target_audience": "global/en"}},
  ...
]

Return ONLY the JSON array."""

            response = ai_client.generate(
                prompt=prompt,
                system_prompt="You are an SEO expert. Return valid JSON only.",
                max_tokens=1500
            )
            
            import json
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            keywords = json.loads(response)
            
            # 서브카테고리 정보 추가
            for kw in keywords:
                kw["subcategory"] = subcat["name"]
                kw["subcategory_slug"] = subcat["slug"]
            
            all_keywords.extend(keywords)
        
        state["keywords"] = all_keywords
        state["keywords_generated_at"] = datetime.now().isoformat()
        state["node_2_status"] = "success"
        
        logger.info(f"[노드2] 키워드 {len(all_keywords)}개 생성 완료")
        
    except Exception as e:
        logger.error(f"[노드2] 키워드 생성 실패: {e}")
        state["error"] = str(e)
        state["node_2_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 3: 블로그 글 작성
# ==============================================================================
def blog_writer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    키워드를 기반으로 블로그 글을 작성합니다. (MCP 연동 가능)
    
    Args:
        state: 파이프라인 상태 (keywords 포함)
    
    Returns:
        업데이트된 상태 (generated_posts 추가)
    """
    logger.info("[노드3] 블로그 글 작성 시작")
    
    keywords = state.get("keywords", [])
    if not keywords:
        state["error"] = "키워드가 없습니다"
        return state
    
    try:
        ai_client = get_ai_client()
        prompts_config = load_json("prompts.json")
        system_prompt = prompts_config.get("system_prompt", {}).get("base", "")
        
        generated_posts = []
        
        # 상위 3개 키워드만 선택 (비용 최적화)
        selected_keywords = keywords[:3]
        
        for kw in selected_keywords:
            keyword = kw["keyword"]
            subcat = kw.get("subcategory", "General")
            
            logger.info(f"[노드3] 글 작성 중: {keyword}")
            
            prompt = f"""Write a comprehensive blog post about: "{keyword}"

Requirements:
- 1500-2500 words
- Include primary keyword in: title, first 100 words, one H2, meta description
- Use H2/H3 headers, bullet points, tables
- End with clear next steps
- Make it actionable and specific
- Avoid generic AI phrases

Format as JSON:
{{
  "title": "SEO-optimized title (50-60 chars)",
  "meta_description": "Compelling description (150-160 chars)",
  "slug": "url-friendly-slug",
  "content": "Full HTML content",
  "excerpt": "2-3 sentence summary",
  "tags": ["tag1", "tag2", "tag3"],
  "estimated_read_time": 5,
  "affiliate_opportunities": ["product1"],
  "internal_link_suggestions": ["topic1"]
}}

Return ONLY the JSON object."""

            response = ai_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=8000
            )
            
            import json
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            post = json.loads(response)
            post["keyword"] = keyword
            post["subcategory"] = subcat
            post["generated_at"] = datetime.now().isoformat()
            post["status"] = "generated"
            
            # 파일로 저장
            slug = post.get("slug", "post")[:50]
            filename = f"post_{generate_timestamp()}_{slug}.json"
            save_json(post, filename)
            
            generated_posts.append({
                "filename": filename,
                "title": post.get("title"),
                "keyword": keyword,
                "status": "saved"
            })
        
        state["generated_posts"] = generated_posts
        state["posts_generated_at"] = datetime.now().isoformat()
        state["node_3_status"] = "success"
        
        logger.info(f"[노드3] {len(generated_posts)}개 글 작성 완료")
        
    except Exception as e:
        logger.error(f"[노드3] 블로그 글 작성 실패: {e}")
        state["error"] = str(e)
        state["node_3_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 4: SEO 최적화
# ==============================================================================
def seo_optimizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    생성된 글의 SEO를 최적화합니다.
    
    Args:
        state: 파이프라인 상태 (generated_posts 포함)
    
    Returns:
        업데이트된 상태 (optimized_posts 추가)
    """
    logger.info("[노드4] SEO 최적화 시작")
    
    generated_posts = state.get("generated_posts", [])
    if not generated_posts:
        state["error"] = "생성된 글이 없습니다"
        return state
    
    try:
        optimized_posts = []
        
        for post_info in generated_posts:
            filename = post_info["filename"]
            
            # SEO 최적화 로직 (scripts/seo_optimizer.py에서 재사용)
            from scripts.seo_optimizer import optimize_seo
            from scripts.common import load_output_json, save_json
            
            post_data = load_output_json(filename)
            result = optimize_seo(post_data)
            
            optimized_data = result["optimized_data"]
            optimized_filename = filename.replace(".json", "_optimized.json")
            save_json(optimized_data, optimized_filename)
            
            optimized_posts.append({
                "original_filename": filename,
                "filename": optimized_filename,
                "title": optimized_data.get("title"),
                "seo_score": result["seo_score"],
                "status": "optimized"
            })
            
            logger.info(f"[노드4] SEO 최적화 완료: {filename} (점수: {result['seo_score']}/100)")
        
        state["optimized_posts"] = optimized_posts
        state["seo_optimized_at"] = datetime.now().isoformat()
        state["node_4_status"] = "success"
        
    except Exception as e:
        logger.error(f"[노드4] SEO 최적화 실패: {e}")
        state["error"] = str(e)
        state["node_4_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 5: 흥미도/참여도 체크
# ==============================================================================
def engagement_checker(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    글의 흥미도와 참여도를 예측합니다.
    
    Args:
        state: 파이프라인 상태 (optimized_posts 포함)
    
    Returns:
        업데이트된 상태 (engagement_scores 추가)
    """
    logger.info("[노드5] 흥미도 체크 시작")
    
    optimized_posts = state.get("optimized_posts", [])
    if not optimized_posts:
        state["error"] = "최적화된 글이 없습니다"
        return state
    
    try:
        ai_client = get_ai_client()
        engagement_scores = []
        
        for post_info in optimized_posts:
            from scripts.common import load_output_json
            
            post_data = load_output_json(post_info["filename"])
            title = post_data.get("title", "")
            content = post_data.get("content", "")[:2000]  # 처음 2000자만
            
            prompt = f"""Analyze this blog post for engagement potential:

Title: {title}

Content preview: {content}...

Evaluate and return JSON:
{{
  "hook_score": 0-100,  // Opening hook effectiveness
  "readability_score": 0-100,  // How easy to read
  "actionability_score": 0-100,  // Clear next steps
  "uniqueness_score": 0-100,  // Unique value vs competitors
  "overall_engagement": 0-100,  // Overall predicted engagement
  "improvement_suggestions": ["suggestion1", "suggestion2"]
}}

Return ONLY the JSON object."""

            response = ai_client.generate(
                prompt=prompt,
                system_prompt="You are a content engagement expert. Return valid JSON only.",
                max_tokens=1000
            )
            
            import json
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            score = json.loads(response)
            score["post_filename"] = post_info["filename"]
            score["title"] = title
            
            engagement_scores.append(score)
            
            logger.info(f"[노드5] 흥미도 체크 완료: {title} (점수: {score.get('overall_engagement', 0)}/100)")
        
        state["engagement_scores"] = engagement_scores
        state["engagement_checked_at"] = datetime.now().isoformat()
        state["node_5_status"] = "success"
        
    except Exception as e:
        logger.error(f"[노드5] 흥미도 체크 실패: {e}")
        state["error"] = str(e)
        state["node_5_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 6: 검토 (자동 또는 수동)
# ==============================================================================
def reviewer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 검토 후 WordPress 발행 준비 상태로 만듭니다.
    
    Args:
        state: 파이프라인 상태 (engagement_scores 포함)
    
    Returns:
        업데이트된 상태 (review_status 추가)
    """
    logger.info("[노드6] 검토 노드 시작")
    
    engagement_scores = state.get("engagement_scores", [])
    if not engagement_scores:
        state["error"] = "흥미도 점수가 없습니다"
        return state
    
    try:
        # 자동 검토: 흥미도 60점 이상이면 자동 승인
        auto_approve_threshold = state.get("config", {}).get("auto_approve_threshold", 60)
        
        review_results = []
        
        for score in engagement_scores:
            engagement = score.get("overall_engagement", 0)
            
            if engagement >= auto_approve_threshold:
                status = "auto_approved"
                action = "publish"
            else:
                status = "needs_manual_review"
                action = "wait"
            
            review_results.append({
                "post_filename": score["post_filename"],
                "title": score["title"],
                "engagement_score": engagement,
                "review_status": status,
                "action": action
            })
        
        state["review_results"] = review_results
        state["review_completed_at"] = datetime.now().isoformat()
        state["node_6_status"] = "success"
        
        logger.info(f"[노드6] 검토 완료: {len(review_results)}개 글 처리")
        
    except Exception as e:
        logger.error(f"[노드6] 검토 실패: {e}")
        state["error"] = str(e)
        state["node_6_status"] = "failed"
    
    return state

# ==============================================================================
# 노드 7: WordPress 발행
# ==============================================================================
def wordpress_publisher(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    승인된 글을 WordPress에 발행합니다.
    
    Args:
        state: 파이프라인 상태 (review_results 포함)
    
    Returns:
        업데이트된 상태 (published_posts 추가)
    """
    logger.info("[노드7] WordPress 발행 시작")
    
    review_results = state.get("review_results", [])
    posts_to_publish = [r for r in review_results if r.get("action") == "publish"]
    
    if not posts_to_publish:
        logger.info("[노드7] 발행할 글이 없습니다")
        state["published_posts"] = []
        return state
    
    try:
        from scripts.wp_publisher import publish_post
        
        published_posts = []
        
        for post_info in posts_to_publish:
            filename = post_info["post_filename"]
            
            result = publish_post(filename)
            
            if result:
                published_posts.append({
                    "filename": filename,
                    "title": post_info["title"],
                    "wp_url": result.get("url"),
                    "wp_post_id": result.get("id"),
                    "status": "published"
                })
                
                logger.info(f"[노드7] 발행 완료: {post_info['title']}")
            else:
                logger.error(f"[노드7] 발행 실패: {filename}")
        
        state["published_posts"] = published_posts
        state["publishing_completed_at"] = datetime.now().isoformat()
        state["node_7_status"] = "success"
        
    except Exception as e:
        logger.error(f"[노드7] WordPress 발행 실패: {e}")
        state["error"] = str(e)
        state["node_7_status"] = "failed"
    
    return state

# ==============================================================================
# 조건부 엣지: 자동 승인 여부
# ==============================================================================
def should_auto_publish(state: Dict[str, Any]) -> str:
    """
    자동 발행 여부를 결정하는 조건부 엣지 함수.
    
    Returns:
        "auto_publish" 또는 "manual_review"
    """
    auto_approve = state.get("config", {}).get("auto_approve", False)
    
    if auto_approve:
        return "auto_publish"
    else:
        return "manual_review"

# ==============================================================================
# 인간 검토 노드 (대화형)
# ==============================================================================
def human_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    인간 검토자가 승인할 때까지 대기하는 노드.
    실제 구현에서는 웹소켓이나 폴링 방식으로 처리.
    
    Args:
        state: 파이프라인 상태
    
    Returns:
        업데이트된 상태
    """
    logger.info("[노드-H] 인간 검토 대기 중...")
    
    # 실제 구현에서는 검토 대기열에 추가하고
    # 외부에서 승인될 때까지 상태를 유지
    state["waiting_for_review"] = True
    state["review_queue_updated_at"] = datetime.now().isoformat()
    
    return state