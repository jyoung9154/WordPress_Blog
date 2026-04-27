#!/usr/bin/env python3
# ==============================================================================
# 제휴링크 자동 삽입 스크립트
# ==============================================================================
# 이 파일의 역할: 블로그 포스트 내 특정 키워드에 제휴링크를 자동 삽입
# 사용법: python scripts/affiliate_inserter.py --file "output/post_xxx.json"
#        python scripts/affiliate_inserter.py --latest
# ==============================================================================

import sys
import os
import json
import argparse
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    load_environment,
    setup_logging,
    load_json,
    save_json,
    load_output_json,
    list_output_files,
    generate_timestamp,
    ROOT_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("affiliate_inserter", "affiliate_inserter.log")

# ==============================================================================
# 상수 정의
# ==============================================================================
MAX_AFFILIATE_LINKS = 3  # 글당 최대 제휴링크 수

# ==============================================================================
# 제휴링크 삽입기 클래스
# ==============================================================================
class AffiliateInserter:
    """
    블로그 포스트에 제휴링크를 자동 삽입하는 클래스
    """
    
    def __init__(self, affiliates_config: dict):
        """
        AffiliateInserter 초기화
        
        Args:
            affiliates_config: affiliates.json 설정 데이터
        """
        self.config = affiliates_config
        self.insertion_rules = affiliates_config.get("insertion_rules", {})
        self.products = affiliates_config.get("products", {})
        self.keyword_mapping = affiliates_config.get("keyword_mapping", {})
        self.tracking_params = affiliates_config.get("tracking_params", {})
        
        # 삽입된 링크 추적
        self.inserted_links = []
    
    def build_affiliate_url(self, base_url: str) -> str:
        """
        제휴 URL에 트래킹 파라미터를 추가합니다.
        
        Args:
            base_url: 기본 제휴 URL
        
        Returns:
            트래킹 파라미터가 추가된 URL
        """
        if not base_url:
            return ""
        
        # 이미 쿼리 파라미터가 있는지 확인
        separator = "&" if "?" in base_url else "?"
        
        params = []
        for key, value in self.tracking_params.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    params.append(f"{key}[{sub_key}]={sub_value}")
            else:
                params.append(f"{key}={value}")
        
        if params:
            return base_url + separator + "&".join(params)
        
        return base_url
    
    def get_anchor_text(self, product_name: str) -> str:
        """
        제품에 대한 앵커 텍스트를 가져옵니다.
        
        Args:
            product_name: 제품 이름
        
        Returns:
            앵커 텍스트
        """
        product = self.products.get(product_name, {})
        anchor_options = product.get("anchor_text_options", [])
        
        if anchor_options:
            return anchor_options[0]
        
        return f"sign up with {product_name}"
    
    def find_insertion_points(self, content: str, keyword: str) -> List[Dict]:
        """
        키워드의 삽입 포인트를 찾습니다.
        
        Args:
            content: HTML 콘텐츠
            keyword: 매핑할 키워드
        
        Returns:
            삽입 포인트 리스트
        """
        points = []
        keyword_lower = keyword.lower()
        
        # 첫 번째 언급 위치 찾기
        pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(content))
        
        if matches:
            # 첫 번째 언급
            first_match = matches[0]
            points.append({
                "position": first_match.start(),
                "type": "first_mention",
                "match": first_match.group()
            })
            
            # 비교 테이블 위치 (如果有)
            if "comparison" in self.insertion_rules.get("placement", []):
                table_pattern = re.compile(r'<table[^>]*>.*?</table>', re.IGNORECASE | re.DOTALL)
                tables = list(table_pattern.finditer(content))
                if tables:
                    points.append({
                        "position": tables[0].start(),
                        "type": "comparison",
                        "match": "table"
                    })
            
            # 결론 CTA 위치
            if "conclusion" in self.insertion_rules.get("placement", []):
                # 마지막 </p> 또는 </h2> 위치 찾기
                conclusion_pattern = re.compile(r'(</p>|</h2>|</h3>)', re.IGNORECASE)
                conclusions = list(conclusion_pattern.finditer(content))
                if conclusions:
                    points.append({
                        "position": conclusions[-1].end(),
                        "type": "conclusion",
                        "match": "conclusion"
                    })
        
        return points
    
    def insert_affiliate_link(self, content: str, keyword: str, product_name: str) -> str:
        """
        콘텐츠에 제휴링크를 삽입합니다.
        
        Args:
            content: HTML 콘텐츠
            keyword: 매핑 키워드
            product_name: 제품 이름
        
        Returns:
            링크가 삽입된 콘텐츠
        """
        product = self.products.get(product_name, {})
        if not product:
            logger.warning(f" 제품을 찾을 수 없습니다: {product_name}")
            return content
        
        base_url = product.get("affiliate_url", "")
        if not base_url:
            logger.warning(f"{product_name}에 제휴 URL이 설정되지 않았습니다.")
            return content
        
        # 트래킹 파라미터 추가
        affiliate_url = self.build_affiliate_url(base_url)
        
        # 앵커 텍스트 가져오기
        anchor_text = self.get_anchor_text(product_name)
        
        # HTML 템플릿
        html_template = self.insertion_rules.get("html_template", 
            "<a href='{url}' rel='nofollow sponsored' target='_blank'>{text}</a>")
        
        affiliate_html = html_template.format(url=affiliate_url, text=anchor_text)
        
        # 삽입 포인트 찾기
        points = self.find_insertion_points(content, keyword)
        
        if not points:
            logger.info(f"키워드 '{keyword}'의 삽입 포인트를 찾을 수 없습니다.")
            return content
        
        # 첫 번째 포인트에 삽입
        point = points[0]
        position = point["position"]
        
        # 기존 텍스트 찾기
        keyword_lower = keyword.lower()
        pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b', re.IGNORECASE)
        match = pattern.search(content, position)
        
        if match:
            # 키워드를 링크로 감싸기
            before = content[:match.start()]
            after = content[match.end():]
            content = before + affiliate_html + after
            
            self.inserted_links.append({
                "keyword": keyword,
                "product": product_name,
                "url": affiliate_url,
                "type": point["type"]
            })
            
            logger.info(f"제휴링크 삽입 완료: {keyword} -> {product_name}")
        else:
            logger.warning(f"키워드 '{keyword}'를 콘텐츠에서 찾을 수 없습니다.")
        
        return content
    
    def insert_affiliate_links(self, content: str, category_slug: str, 
                               affiliate_opportunities: List[str]) -> str:
        """
        콘텐츠에 여러 제휴링크를 삽입합니다.
        
        Args:
            content: HTML 콘텐츠
            category_slug: 카테고리 슬러그
            affiliate_opportunities: 제휴 기회 제품 리스트
        
        Returns:
            제휴링크가 삽입된 콘텐츠
        """
        logger.info(f"제휴링크 삽입 시작 (카테고리: {category_slug})")
        
        # 카테고리에 적합한 제품 찾기
        category_products = []
        for product_name, product_data in self.products.items():
            best_for = product_data.get("best_for", [])
            if category_slug in best_for:
                category_products.append(product_name)
        
        # 키워드 매핑에서 찾기
        inserted_count = 0
        max_links = self.insertion_rules.get("max_per_post", MAX_AFFILIATE_LINKS)
        
        for keyword, mapping in self.keyword_mapping.items():
            if inserted_count >= max_links:
                break
            
            product = mapping.get("product", "")
            
            # 제품이 카테고리에 적합한지 확인
            if product not in category_products:
                continue
            
            # 이미 삽입된 제품인지 확인
            if any(link["product"] == product for link in self.inserted_links):
                continue
            
            # 콘텐츠에 키워드가 있는지 확인
            if keyword.lower() not in content.lower():
                continue
            
            content = self.insert_affiliate_link(content, keyword, product)
            inserted_count += 1
        
        # 추가 제휴 기회 처리
        for product_name in affiliate_opportunities:
            if inserted_count >= max_links:
                break
            
            if product_name not in [link["product"] for link in self.inserted_links]:
                product = self.products.get(product_name, {})
                if product and product.get("affiliate_url"):
                    # 키워드 매핑에서 해당 제품의 키워드 찾기
                    for keyword, mapping in self.keyword_mapping.items():
                        if mapping.get("product") == product_name:
                            content = self.insert_affiliate_link(content, keyword, product_name)
                            inserted_count += 1
                            break
        
        return content
    
    def add_disclosure(self, content: str) -> str:
        """
        제휴 공개 문구를 추가합니다.
        
        Args:
            content: HTML 콘텐츠
        
        Returns:
            공개 문구가 추가된 콘텐츠
        """
        disclosure_required = self.insertion_rules.get("disclosure_required", True)
        if not disclosure_required:
            return content
        
        disclosure_text = self.insertion_rules.get("disclosure_text", "")
        disclosure_position = self.insertion_rules.get("disclosure_position", "bottom")
        
        if not disclosure_text:
            return content
        
        disclosure_html = f'<p class="affiliate-disclosure">{disclosure_text}</p>'
        
        if disclosure_position == "top":
            content = disclosure_html + content
        else:
            content = content + disclosure_html
        
        return content
    
    def process_post(self, post_data: dict) -> dict:
        """
        포스트 데이터를 처리하여 제휴링크를 삽입합니다.
        
        Args:
            post_data: 포스트 데이터
        
        Returns:
            처리된 포스트 데이터
        """
        content = post_data.get("content", "")
        category_slug = post_data.get("category_slug", "")
        affiliate_opportunities = post_data.get("affiliate_opportunities", [])
        
        # 초기화
        self.inserted_links = []
        
        # 제휴링크 삽입
        content = self.insert_affiliate_links(content, category_slug, affiliate_opportunities)
        
        # 공개 문구 추가
        content = self.add_disclosure(content)
        
        # 결과 저장
        post_data["content"] = content
        post_data["affiliate_links_inserted"] = self.inserted_links
        post_data["affiliate_disclosure_added"] = True
        
        return post_data

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="포스트에 제휴링크를 자동 삽입합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/affiliate_inserter.py --file "post_20250101_abc123.json"
  python scripts/affiliate_inserter.py --latest
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", type=str, help="output/ 폴더의 파일명")
    group.add_argument("--latest", "-l", action="store_true", help="가장 최근 파일 자동 선택")
    
    args = parser.parse_args()
    
    # 환경변수 로드
    load_environment()
    
    # 파일 선택
    if args.file:
        filename = args.file
        if not filename.endswith(".json"):
            filename += ".json"
    else:
        files = list_output_files()
        if not files:
            logger.error("output/ 폴더에 파일이 없습니다.")
            sys.exit(1)
        filename = sorted(files, reverse=True)[0]
        logger.info(f"가장 최근 파일 선택: {filename}")
    
    # 파일 로드
    try:
        post_data = load_output_json(filename)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {filename}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        sys.exit(1)
    
    # 제휴 설정 로드
    try:
        affiliates_config = load_json("affiliates.json")
    except FileNotFoundError as e:
        logger.error(f"제휴 설정 파일을 찾을 수 없습니다: {e}")
        sys.exit(1)
    
    # 제휴링크 삽입
    inserter = AffiliateInserter(affiliates_config)
    processed_data = inserter.process_post(post_data)
    
    # 결과 저장
    affiliate_filename = filename.replace('.json', '_affiliate.json')
    if save_json(processed_data, affiliate_filename):
        logger.info(f"제휴링크 삽입 결과 저장: {affiliate_filename}")
    else:
        logger.error("결과 저장 실패")
        sys.exit(1)
    
    # 결과 출력
    print(f"\n{'='*60}")
    print(f"🔗 제휴링크 삽입 완료!")
    print(f"{'='*60}")
    print(f"제목: {post_data.get('title', 'N/A')}")
    print(f"삽입된 링크 수: {len(inserter.inserted_links)}")
    
    if inserter.inserted_links:
        print(f"\n삽입된 링크:")
        for link in inserter.inserted_links:
            print(f"  - {link['keyword']} -> {link['product']}")
            print(f"    ({link['type']})")
    
    print(f"\n💾 저장 위치: output/{affiliate_filename}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()