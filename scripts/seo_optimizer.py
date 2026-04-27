#!/usr/bin/env python3
# ==============================================================================
# SEO 최적화 스크립트
# ==============================================================================
# 이 파일의 역할: 생성된 블로그 포스트의 SEO를 최적화
# - 키워드 밀도 체크 (1.5~2.5% 유지)
# - 메타 태그 길이 검증
# - H태그 구조 검증
# - 가독성 점수 계산
# - Schema.org JSON-LD 생성
# - 이미지 alt 태그 생성
# 사용법: python scripts/seo_optimizer.py --file "output/post_xxx.json"
#        python scripts/seo_optimizer.py --latest  # 가장 최근 파일
# ==============================================================================

import sys
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

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
logger = setup_logging("seo_optimizer", "seo_optimizer.log")

# ==============================================================================
# 상수 정의
# ==============================================================================
# SEO 최적화 상수
MIN_KEYWORD_DENSITY = 1.5  # 최소 키워드 밀도 (%)
MAX_KEYWORD_DENSITY = 2.5  # 최대 키워드 밀도 (%)
MAX_META_TITLE = 60  # 메타 제목 최대 문자 수
MAX_META_DESCRIPTION = 160  # 메타 설명 최대 문자 수
MIN_PARAGRAPH_LENGTH = 50  # 단락 최소 문자 수
TARGET_READING_TIME = 7  # 목표 읽기 시간 (분)

# ==============================================================================
# SEO 분석 함수
# ==============================================================================
def count_words(text: str) -> int:
    """
    텍스트의 단어 수를 계산합니다.
    
    Args:
        text: 분석할 텍스트
    
    Returns:
        단어 수
    """
    # HTML 태그 제거
    soup = BeautifulSoup(text, 'html.parser')
    plain_text = soup.get_text()
    
    # 단어 분리 (영문 기준)
    words = re.findall(r'\b[a-zA-Z]+\b', plain_text.lower())
    return len(words)

def calculate_keyword_density(content: str, keyword: str) -> float:
    """
    키워드 밀도를 계산합니다.
    
    Args:
        content: 본문 HTML
        keyword: 대상 키워드
    
    Returns:
        키워드 밀도 (%)
    """
    word_count = count_words(content)
    if word_count == 0:
        return 0.0
    
    # 키워드 빈도수 계산 (대소문자 무시)
    keyword_lower = keyword.lower()
    content_lower = content.lower()
    
    # 단어 경계로 키워드 찾기
    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
    keyword_count = len(re.findall(pattern, content_lower))
    
    density = (keyword_count / word_count) * 100
    return round(density, 2)

def check_heading_structure(content: str) -> dict:
    """
    H태그 구조를 검증합니다.
    
    Args:
        content: 본문 HTML
    
    Returns:
        검증 결과 딕셔너리
    """
    soup = BeautifulSoup(content, 'html.parser')
    
    h1_tags = soup.find_all('h1')
    h2_tags = soup.find_all('h2')
    h3_tags = soup.find_all('h3')
    
    result = {
        "h1_count": len(h1_tags),
        "h2_count": len(h2_tags),
        "h3_count": len(h3_tags),
        "has_h1": len(h1_tags) > 0,
        "has_h2": len(h2_tags) > 0,
        "h2_titles": [h.get_text().strip()[:50] for h in h2_tags],
        "issues": []
    }
    
    # 검증
    if len(h1_tags) > 1:
        result["issues"].append("H1 태그가 2개 이상입니다. SEO 최적화를 위해 H1은 1개만 사용하세요.")
    
    if len(h1_tags) == 0:
        result["issues"].append("H1 태그가 없습니다. 제목용 H1을 추가해주세요.")
    
    if len(h2_tags) < 3:
        result["issues"].append(f"H2 태그가 {len(h2_tags)}개입니다. 최소 3개 이상 권장합니다.")
    
    return result

def calculate_readability_score(content: str) -> dict:
    """
    가독성 점수를 계산합니다. (Flesch Reading Ease 기준)
    
    Args:
        content: 본문 HTML
    
    Returns:
        가독성 분석 결과
    """
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    
    # 문장 분리
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 단어 분리
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    
    if not sentences or not words:
        return {"score": 0, "grade": "N/A", "issues": ["내용이 너무 짧습니다."]}
    
    # 평균 문장 길이
    avg_sentence_length = len(words) / len(sentences)
    
    # 평균 단어 길이 (음절 수로 추정)
    total_syllables = sum(count_syllables(word) for word in words)
    avg_syllables_per_word = total_syllables / len(words) if words else 0
    
    # Flesch Reading Ease 공식
    # 206.835 - 1.015 * (단어 수 / 문장 수) - 84.6 * (음절 수 / 단어 수)
    readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    readability_score = max(0, min(100, readability_score))  # 0-100 범위 제한
    
    # 등급 매핑
    if readability_score >= 90:
        grade = "5학년 수준 (매우 쉬움)"
    elif readability_score >= 80:
        grade = "6학년 수준 (쉬움)"
    elif readability_score >= 70:
        grade = "7학년 수준 (약간 쉬움)"
    elif readability_score >= 60:
        grade = "8-9학년 수준 (보통)"
    elif readability_score >= 50:
        grade = "10-12학년 수준 (약간 어려움)"
    elif readability_score >= 30:
        grade = "대학 수준 (어려움)"
    else:
        grade = "대학원 수준 (매우 어려움)"
    
    result = {
        "score": round(readability_score, 1),
        "grade": grade,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "avg_syllables_per_word": round(avg_syllables_per_word, 1),
        "total_words": len(words),
        "total_sentences": len(sentences),
        "issues": []
    }
    
    # 권장 범위 체크
    if avg_sentence_length > 25:
        result["issues"].append("평균 문장 길이가 깁니다. 20단어 이하로 줄여주세요.")
    
    if avg_syllables_per_word > 1.7:
        result["issues"].append("평균 단어 길이가 깁니다. 더 간단한 단어를 사용해주세요.")
    
    return result

def count_syllables(word: str) -> int:
    """
    단어의 음절 수를 추정합니다.
    
    Args:
        word: 단어
    
    Returns:
        음절 수
    """
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    
    #无声 e 처리
    if word.endswith("e"):
        count -= 1
    
    return max(1, count)

def generate_schema_markup(post_data: dict) -> dict:
    """
    Schema.org JSON-LD 구조화 데이터를 생성합니다.
    
    Args:
        post_data: 포스트 데이터
    
    Returns:
        Schema.org JSON-LD 데이터
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post_data.get("title", ""),
        "description": post_data.get("meta_description", ""),
        "datePublished": post_data.get("generated_at", datetime.now().isoformat()),
        "dateModified": post_data.get("generated_at", datetime.now().isoformat()),
        "author": {
            "@type": "Person",
            "name": "Financial Guide",
            "url": post_data.get("author_url", "")
        },
        "publisher": {
            "@type": "Organization",
            "name": "Financial Guide Blog",
            "logo": {
                "@type": "ImageObject",
                "url": post_data.get("site_logo", "")
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": post_data.get("permalink", "")
        },
        "articleSection": post_data.get("category", ""),
        "keywords": ", ".join(post_data.get("tags", [])),
        "wordCount": count_words(post_data.get("content", "")),
        "timeRequired": f"PT{post_data.get('estimated_read_time', 5)}M"
    }
    
    return schema

def add_image_alt_tags(content: str, keyword: str) -> str:
    """
    이미지 alt 태그를 자동 생성합니다.
    
    Args:
        content: 본문 HTML
        keyword: 주요 키워드
    
    Returns:
        alt 태그가 추가된 HTML
    """
    soup = BeautifulSoup(content, 'html.parser')
    images = soup.find_all('img')
    
    for i, img in enumerate(images):
        if not img.get('alt'):
            # alt 태그가 없는 이미지에 자동 생성
            alt_text = f"{keyword} - Image {i+1}"
            img['alt'] = alt_text
    
    return str(soup)

def validate_meta_tags(post_data: dict) -> dict:
    """
    메타 태그를 검증합니다.
    
    Args:
        post_data: 포스트 데이터
    
    Returns:
        검증 결과
    """
    result = {
        "title_length": len(post_data.get("title", "")),
        "meta_description_length": len(post_data.get("meta_description", "")),
        "title_ok": True,
        "meta_ok": True,
        "issues": []
    }
    
    # 제목 길이 체크
    if result["title_length"] > MAX_META_TITLE:
        result["title_ok"] = False
        result["issues"].append(f"제목이 {result['title_length']}자입니다. {MAX_META_TITLE}자 이하로 줄여주세요.")
    elif result["title_length"] < 30:
        result["title_ok"] = False
        result["issues"].append(f"제목이 {result['title_length']}자입니다. {MAX_META_TITLE}자 이상으로 작성해주세요.")
    
    # 메타 설명 길이 체크
    if result["meta_description_length"] > MAX_META_DESCRIPTION:
        result["meta_ok"] = False
        result["issues"].append(f"메타 설명이 {result['meta_description_length']}자입니다. {MAX_META_DESCRIPTION}자 이하로 줄여주세요.")
    elif result["meta_description_length"] < 120:
        result["meta_ok"] = False
        result["issues"].append(f"메타 설명이 {result['meta_description_length']}자입니다. {MAX_META_DESCRIPTION}자 이상으로 작성해주세요.")
    
    return result

# ==============================================================================
# SEO 최적화 메인 함수
# ==============================================================================
def optimize_seo(post_data: dict) -> dict:
    """
    포스트의 SEO를 최적화합니다.
    
    Args:
        post_data: 원본 포스트 데이터
    
    Returns:
        SEO 최적화 결과 (점수 + 수정된 데이터)
    """
    logger.info(f"SEO 최적화 시작: {post_data.get('title', 'No title')}")
    
    keyword = post_data.get("keyword", "")
    content = post_data.get("content", "")
    
    # 결과 저장 딕셔너리
    result = {
        "original_data": post_data,
        "optimized_data": post_data.copy(),
        "seo_score": 0,
        "checks": {}
    }
    
    # 1. 키워드 밀도 체크
    keyword_density = calculate_keyword_density(content, keyword)
    result["checks"]["keyword_density"] = {
        "value": keyword_density,
        "target": f"{MIN_KEYWORD_DENSITY}-{MAX_KEYWORD_DENSITY}%",
        "passed": MIN_KEYWORD_DENSITY <= keyword_density <= MAX_KEYWORD_DENSITY,
        "message": f"키워드 밀도: {keyword_density}%"
    }
    
    # 2. H태그 구조 검증
    heading_check = check_heading_structure(content)
    result["checks"]["heading_structure"] = heading_check
    result["checks"]["heading_structure"]["passed"] = len(heading_check["issues"]) == 0
    
    # 3. 가독성 점수 계산
    readability = calculate_readability_score(content)
    result["checks"]["readability"] = readability
    result["checks"]["readability"]["passed"] = readability["score"] >= 60
    
    # 4. 메타 태그 검증
    meta_validation = validate_meta_tags(post_data)
    result["checks"]["meta_tags"] = meta_validation
    result["checks"]["meta_tags"]["passed"] = meta_validation["title_ok"] and meta_validation["meta_ok"]
    
    # 5. Schema.org JSON-LD 생성
    schema = generate_schema_markup(post_data)
    result["checks"]["schema_markup"] = {
        "generated": True,
        "schema": schema
    }
    
    # 6. 이미지 alt 태그 추가
    optimized_content = add_image_alt_tags(content, keyword)
    result["optimized_data"]["content"] = optimized_content
    result["optimized_data"]["schema_markup"] = schema
    
    # SEO 점수 계산 (100점 만점)
    score = 0
    if result["checks"]["keyword_density"]["passed"]:
        score += 25
    if result["checks"]["heading_structure"]["passed"]:
        score += 25
    if result["checks"]["readability"]["passed"]:
        score += 25
    if result["checks"]["meta_tags"]["passed"]:
        score += 25
    
    result["seo_score"] = score
    result["optimized_data"]["seo_score"] = score
    result["optimized_data"]["seo_analysis"] = result["checks"]
    
    logger.info(f"SEO 최적화 완료. 점수: {score}/100")
    
    return result

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="생성된 포스트의 SEO를 최적화합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        # 가장 최근 파일 선택
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
    
    # SEO 최적화 실행
    result = optimize_seo(post_data)
    
    # 결과 저장
    optimized_data = result["optimized_data"]
    optimized_filename = filename.replace(".json", "_optimized.json")
    
    if save_json(optimized_data, optimized_filename):
        logger.info(f"최적화 결과 저장: {optimized_filename}")
    else:
        logger.error("최적화 결과 저장 실패")
        sys.exit(1)
    
    # 결과 출력
    print(f"\n{'='*60}")
    print(f"🔍 SEO 분석 결과")
    print(f"{'='*60}")
    print(f"제목: {post_data.get('title', 'N/A')}")
    print(f"키워드: {post_data.get('keyword', 'N/A')}")
    print(f"\n📊 SEO 점수: {result['seo_score']}/100")
    print(f"\n--- 체크리스트 ---")
    
    for check_name, check_data in result["checks"].items():
        status = "✅" if check_data.get("passed", False) else "❌"
        print(f"{status} {check_name}: {check_data.get('message', check_data.get('value', 'N/A'))}")
    
    if result["checks"].get("heading_structure", {}).get("issues"):
        print("\n⚠️ H태그 이슈:")
        for issue in result["checks"]["heading_structure"]["issues"]:
            print(f"  - {issue}")
    
    if result["checks"].get("readability", {}).get("issues"):
        print("\n⚠️ 가독성 이슈:")
        for issue in result["checks"]["readability"]["issues"]:
            print(f"  - {issue}")
    
    if result["checks"].get("meta_tags", {}).get("issues"):
        print("\n⚠️ 메타 태그 이슈:")
        for issue in result["checks"]["meta_tags"]["issues"]:
            print(f"  - {issue}")
    
    print(f"\n💾 저장 위치: output/{optimized_filename}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()