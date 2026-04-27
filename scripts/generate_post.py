#!/usr/bin/env python3
# ==============================================================================
# AI 글 생성 스크립트
# ==============================================================================
# 이 파일의 역할: Claude API를 사용하여 블로그 포스트를 자동 생성
# 사용법: python scripts/generate_post.py --keyword "your keyword"
#        python scripts/generate_post.py --category "investing-beginners"
#        python scripts/generate_post.py --random  # 랜덤 키워드 선택
# ==============================================================================

import sys
import os
import json
import argparse
import random
from pathlib import Path

# scripts 폴더 내의 common.py를 임포트하기 위해 경로 추가
sys.path.insert(0, str(Path(__file__).parent))
from common import (
    load_environment,
    setup_logging,
    load_json,
    save_json,
    get_claude_client,
    generate_timestamp,
    sanitize_filename,
    ROOT_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("generate_post", "generate_post.log")

# ==============================================================================
# 상수 정의
# ==============================================================================
MAX_RETRIES = 3  # 최대 재시도 횟수
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# ==============================================================================
# 키워드 선택 함수
# ==============================================================================
def select_keyword_by_priority(topics_data: dict) -> dict:
    """
    우선순위에 따라 키워드를 선택합니다.
    
    Args:
        topics_data: topics.json 데이터
    
    Returns:
        선택된 키워드 정보 (keyword, category, competition 등)
    """
    categories = topics_data.get("categories", [])
    
    # 우선순위 순으로 정렬
    sorted_categories = sorted(categories, key=lambda x: x.get("priority", 5))
    
    for category in sorted_categories:
        keywords = category.get("keywords", [])
        if keywords:
            # 가장 경쟁이 낮은 키워드 선택
            sorted_keywords = sorted(keywords, key=lambda k: 
                {"low": 0, "medium": 1, "high": 2}.get(k.get("competition", "medium"), 1)
            )
            selected_keyword = sorted_keywords[0]
            return {
                "keyword": selected_keyword["keyword"],
                "category": category["name"],
                "category_slug": category["slug"],
                "competition": selected_keyword.get("competition", "medium"),
                "cpc_range": selected_keyword.get("cpc_range", ""),
                "custom_prompt": category.get("custom_prompt", ""),
                "affiliate_products": category.get("affiliate_products", [])
            }
    
    return None

def select_random_keyword(topics_data: dict) -> dict:
    """
    랜덤하게 키워드를 선택합니다.
    
    Args:
        topics_data: topics.json 데이터
    
    Returns:
        선택된 키워드 정보
    """
    categories = topics_data.get("categories", [])
    all_keywords = []
    
    for category in categories:
        for keyword in category.get("keywords", []):
            all_keywords.append({
                "keyword": keyword["keyword"],
                "category": category["name"],
                "category_slug": category["slug"],
                "competition": keyword.get("competition", "medium"),
                "cpc_range": keyword.get("cpc_range", ""),
                "custom_prompt": category.get("custom_prompt", ""),
                "affiliate_products": category.get("affiliate_products", [])
            })
    
    return random.choice(all_keywords) if all_keywords else None

def find_keyword_in_topics(topics_data: dict, keyword: str) -> dict:
    """
    특정 키워드가 어느 카테고리에 속하는지 찾습니다.
    
    Args:
        topics_data: topics.json 데이터
        keyword: 찾을 키워드
    
    Returns:
        키워드 정보 또는 None
    """
    for category in topics_data.get("categories", []):
        for kw in category.get("keywords", []):
            if kw["keyword"].lower() == keyword.lower():
                return {
                    "keyword": kw["keyword"],
                    "category": category["name"],
                    "category_slug": category["slug"],
                    "competition": kw.get("competition", "medium"),
                    "cpc_range": kw.get("cpc_range", ""),
                    "custom_prompt": category.get("custom_prompt", ""),
                    "affiliate_products": category.get("affiliate_products", [])
                }
    return None

# ==============================================================================
# 프롬프트 생성 함수
# ==============================================================================
def build_prompt(keyword_info: dict, prompts_data: dict) -> str:
    """
    AI에게 전달할 프롬프트를 구성합니다.
    
    Args:
        keyword_info: 선택된 키워드 정보
        prompts_data: prompts.json 데이터
    
    Returns:
        완성된 프롬프트 문자열
    """
    # 기본 시스템 프롬프트 가져오기
    system_prompt = prompts_data.get("system_prompt", {}).get("base", "")
    
    # 카테고리별 커스텀 프롬프트
    category_slug = keyword_info.get("category_slug", "")
    category_prompts = prompts_data.get("category_prompts", {})
    category_custom = category_prompts.get(category_slug, {})
    
    # 금지 프롬프트 목록
    forbidden_phrases = prompts_data.get("ai_detection_avoidance", {}).get("forbidden_phrases", [])
    forbidden_list = ", ".join([f'"{phrase}"' for phrase in forbidden_phrases])
    
    # 사용자 정의 프롬프트 (있을 경우)
    custom_prompts = prompts_data.get("custom_prompts", {})
    user_custom = custom_prompts.get(category_slug, "")
    
    # 최종 프롬프트 구성
    final_prompt = f"""{system_prompt}

CATEGORY-SPECIFIC INSTRUCTIONS:
{category_custom.get("tone", "Professional and helpful")}
Target audience assumed knowledge: {category_custom.get("assumed_knowledge", "Basic financial literacy")}
{category_custom.get("key_analogies", [""])[0] if category_custom.get("key_analogies") else ""}

USER'S CUSTOM PROMPT (if any):
{user_custom if user_custom else keyword_info.get("custom_prompt", "")}

ARTICLE KEYWORD: {keyword_info["keyword"]}
ARTICLE CATEGORY: {keyword_info["category"]}
AFFILIATE PRODUCTS TO CONSIDER: {", ".join(keyword_info.get("affiliate_products", []))}

IMPORTANT: 
- Write a complete article based on the keyword above
- Format your response as valid JSON with these exact keys:
  - title (50-60 characters, include primary keyword)
  - meta_description (150-160 characters, compelling and include keyword)
  - slug (URL-friendly, include keyword)
  - content (full HTML with proper H2/H3 structure, 1500-2500 words)
  - excerpt (2-3 sentences summary)
  - tags (array of 3-5 relevant tags)
  - estimated_read_time (number in minutes)
  - affiliate_opportunities (array of mentioned products)
  - internal_link_suggestions (array of related topic suggestions)

PHRASES TO AVOID (AI detection avoidance):
Never use these phrases: {forbidden_list}

Return ONLY the JSON, no additional text or explanation."""
    
    return final_prompt

# ==============================================================================
# 글 생성 함수
# ==============================================================================
def generate_post(keyword_info: dict) -> dict:
    """
    Claude API를 사용하여 블로그 포스트를 생성합니다.
    
    Args:
        keyword_info: 키워드 정보
    
    Returns:
        생성된 포스트 데이터 (JSON)
    """
    logger.info(f"글 생성 시작: {keyword_info['keyword']}")
    logger.info(f"카테고리: {keyword_info['category']}")
    
    # 프롬프트 데이터 로드
    prompts_data = load_json("prompts.json")
    
    # 프롬프트 구성
    prompt = build_prompt(keyword_info, prompts_data)
    
    # Claude API 클라이언트 가져오기
    client = get_claude_client()
    model = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    
    # 재시도 로직
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"API 요청 시도 {attempt + 1}/{MAX_RETRIES}")
            
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                temperature=0.7,
                system="You are an expert financial content writer. Return only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 응답 텍스트 추출
            response_text = response.content[0].text.strip()
            
            # JSON 파싱
            # Markdown 코드 블록 제거 (```json ... ```)
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])  # 첫 줄과 마지막 줄 제거
            
            post_data = json.loads(response_text)
            
            # 메타데이터 추가
            post_data["generated_at"] = datetime.now().isoformat()
            post_data["keyword"] = keyword_info["keyword"]
            post_data["category"] = keyword_info["category"]
            post_data["category_slug"] = keyword_info["category_slug"]
            post_data["competition"] = keyword_info.get("competition", "")
            post_data["cpc_range"] = keyword_info.get("cpc_range", "")
            post_data["status"] = "generated"
            
            logger.info(f"글 생성 성공: {post_data.get('title', 'No title')}")
            return post_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info("재시도합니다...")
            else:
                logger.error("최대 재시도 횟수 초과")
                raise
                
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info("재시도합니다...")
            else:
                raise
    
    return None

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="AI를 사용하여 블로그 포스트를 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/generate_post.py --keyword "how to start investing with $100"
  python scripts/generate_post.py --category "investing-beginners"
  python scripts/generate_post.py --random
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--keyword", "-k", type=str, help="특정 키워드로 생성")
    group.add_argument("--category", "-c", type=str, help="카테고리 내 우선순위 키워드로 생성")
    group.add_argument("--random", "-r", action="store_true", help="랜덤 키워드로 생성")
    
    args = parser.parse_args()
    
    # 환경변수 로드
    load_environment()
    
    # topics.json 로드
    try:
        topics_data = load_json("topics.json")
    except FileNotFoundError as e:
        logger.error(f"설정 파일 오류: {e}")
        sys.exit(1)
    
    # 키워드 선택
    if args.keyword:
        keyword_info = find_keyword_in_topics(topics_data, args.keyword)
        if not keyword_info:
            logger.warning(f"키워드를 찾을 수 없습니다: {args.keyword}")
            logger.info("topics.json에 없는 키워드입니다. 새 키워드로 생성합니다.")
            keyword_info = {
                "keyword": args.keyword,
                "category": "General",
                "category_slug": "general",
                "competition": "medium",
                "cpc_range": "",
                "custom_prompt": "",
                "affiliate_products": []
            }
    elif args.category:
        #指定된 카테고리에서 키워드 선택
        found = False
        for cat in topics_data.get("categories", []):
            if cat["slug"] == args.category and cat.get("keywords"):
                keyword_info = {
                    "keyword": cat["keywords"][0]["keyword"],
                    "category": cat["name"],
                    "category_slug": cat["slug"],
                    "competition": cat["keywords"][0].get("competition", "medium"),
                    "cpc_range": cat["keywords"][0].get("cpc_range", ""),
                    "custom_prompt": cat.get("custom_prompt", ""),
                    "affiliate_products": cat.get("affiliate_products", [])
                }
                found = True
                break
        
        if not found:
            logger.error(f"카테고리를 찾을 수 없습니다: {args.category}")
            sys.exit(1)
    else:
        keyword_info = select_random_keyword(topics_data)
    
    if not keyword_info:
        logger.error("생성할 키워드를 찾을 수 없습니다.")
        sys.exit(1)
    
    # 글 생성
    try:
        post_data = generate_post(keyword_info)
        
        if post_data:
            # 파일명 생성 (타임스탬프 + 슬러그)
            slug = post_data.get("slug", "post")
            safe_slug = sanitize_filename(slug)[:50]
            filename = f"post_{generate_timestamp()}_{safe_slug}.json"
            
            # 파일 저장
            if save_json(post_data, filename):
                logger.info(f"포스트 저장 완료: {filename}")
                print(f"\n{'='*60}")
                print(f"✅ 글 생성 완료!")
                print(f"{'='*60}")
                print(f"제목: {post_data.get('title', 'N/A')}")
                print(f"키워드: {post_data.get('keyword', 'N/A')}")
                print(f"카테고리: {post_data.get('category', 'N/A')}")
                print(f"예상 읽기 시간: {post_data.get('estimated_read_time', 'N/A')}분")
                print(f"저장 위치: output/{filename}")
                print(f"{'='*60}\n")
            else:
                logger.error("포스트 저장 실패")
                sys.exit(1)
        else:
            logger.error("포스트 생성 실패")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"글 생성 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()