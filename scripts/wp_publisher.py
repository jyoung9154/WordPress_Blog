#!/usr/bin/env python3
# ==============================================================================
# WordPress 발행 스크립트
# ==============================================================================
# 이 파일의 역할: 검토가 완료된 포스트를 WordPress REST API로 발행
# 사용법: python scripts/wp_publisher.py --file "output/post_xxx.json"
#        python scripts/wp_publisher.py --latest
# ==============================================================================

import sys
import os
import json
import argparse
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    load_environment,
    setup_logging,
    load_json,
    load_output_json,
    get_wordpress_config,
    generate_timestamp,
    ROOT_DIR
)

# ==============================================================================
# 로거 설정
# ==============================================================================
logger = setup_logging("wp_publisher", "wp_publisher.log")

# ==============================================================================
# WordPress API 클래스
# ==============================================================================
class WordPressPublisher:
    """
    WordPress REST API를 사용하여 포스트를 발행하는 클래스
    """
    
    def __init__(self, site_url: str, username: str, password: str):
        """
        WordPressPublisher 초기화
        
        Args:
            site_url: WordPress 사이트 URL
            username: 사용자명
            password: 애플리케이션 비밀번호
        """
        self.site_url = site_url.rstrip('/')
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        self.username = username
        self.password = password
        
        # Basic Auth 헤더 생성
        credentials = f"{username}:{password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        self.headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }
    
    def check_connection(self) -> bool:
        """
        WordPress API 연결을 확인합니다.
        
        Returns:
            연결 성공 여부
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.api_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WordPress 연결 확인 실패: {e}")
            return False
    
    def get_categories(self) -> list:
        """
        기존 카테고리 목록을 가져옵니다.
        
        Returns:
            카테고리 리스트
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.api_url}/categories",
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                return {cat['name']: cat['id'] for cat in categories}
            else:
                logger.error(f"카테고리 조회 실패: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"카테고리 조회 중 오류: {e}")
            return {}
    
    def create_category(self, name: str, slug: str = None, parent_id: int = None) -> Optional[int]:
        """
        새 카테고리를 생성합니다.
        
        Args:
            name: 카테고리 이름
            slug: 카테고리 슬러그
            parent_id: 부모 카테고리 ID
        
        Returns:
            생성된 카테고리 ID 또는 None
        """
        import requests
        
        data = {'name': name}
        if slug:
            data['slug'] = slug
        if parent_id:
            data['parent'] = parent_id
        
        try:
            response = requests.post(
                f"{self.api_url}/categories",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                category = response.json()
                logger.info(f"카테고리 생성 완료: {name} (ID: {category['id']})")
                return category['id']
            else:
                logger.error(f"카테고리 생성 실패: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"카테고리 생성 중 오류: {e}")
            return None
    
    def get_or_create_category(self, name: str, slug: str = None) -> Optional[int]:
        """
        카테고리가 있으면 가져오고, 없으면 생성합니다.
        
        Args:
            name: 카테고리 이름
            slug: 카테고리 슬러그
        
        Returns:
            카테고리 ID 또는 None
        """
        categories = self.get_categories()
        
        if name in categories:
            logger.info(f"기존 카테고리 사용: {name} (ID: {categories[name]})")
            return categories[name]
        
        return self.create_category(name, slug)
    
    def get_tags(self) -> list:
        """
        기존 태그 목록을 가져옵니다.
        
        Returns:
            태그 딕셔너리 (이름: ID)
        """
        import requests
        
        try:
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                tags = response.json()
                return {tag['name']: tag['id'] for tag in tags}
            else:
                return {}
        except Exception as e:
            logger.error(f"태그 조회 중 오류: {e}")
            return {}
    
    def create_tag(self, name: str, slug: str = None) -> Optional[int]:
        """
        새 태그를 생성합니다.
        
        Args:
            name: 태그 이름
            slug: 태그 슬러그
        
        Returns:
            생성된 태그 ID 또는 None
        """
        import requests
        
        data = {'name': name}
        if slug:
            data['slug'] = slug
        
        try:
            response = requests.post(
                f"{self.api_url}/tags",
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                tag = response.json()
                logger.info(f"태그 생성 완료: {name} (ID: {tag['id']})")
                return tag['id']
            else:
                logger.error(f"태그 생성 실패: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"태그 생성 중 오류: {e}")
            return None
    
    def get_or_create_tags(self, tag_names: list) -> list:
        """
        태그 목록을 가져오거나 생성합니다.
        
        Args:
            tag_names: 태그 이름 리스트
        
        Returns:
            태그 ID 리스트
        """
        existing_tags = self.get_tags()
        tag_ids = []
        
        for name in tag_names:
            if name in existing_tags:
                tag_ids.append(existing_tags[name])
            else:
                tag_id = self.create_tag(name)
                if tag_id:
                    tag_ids.append(tag_id)
        
        return tag_ids
    
    def upload_media(self, image_url: str, title: str) -> Optional[int]:
        """
        이미지를 미디어 라이브러리에 업로드합니다.
        
        Args:
            image_url: 이미지 URL
            title: 이미지 제목
        
        Returns:
            미디어 ID 또는 None
        """
        import requests
        
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"이미지 다운로드 실패: {image_url}")
                return None
            
            image_data = response.content
            image_name = f"featured_image_{generate_timestamp()}.jpg"
            
            # 미디어 업로드
            upload_headers = self.headers.copy()
            upload_headers['Content-Type'] = 'image/jpeg'
            
            files = {
                'file': (image_name, image_data, 'image/jpeg')
            }
            
            data = {
                'title': title,
                'status': 'publish'
            }
            
            response = requests.post(
                f"{self.api_url}/media",
                headers=upload_headers,
                data=data,
                files=files,
                timeout=30
            )
            
            if response.status_code == 201:
                media = response.json()
                logger.info(f"미디어 업로드 완료: {media['source_url']}")
                return media['id']
            else:
                logger.error(f"미디어 업로드 실패: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"미디어 업로드 중 오류: {e}")
            return None
    
    def create_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        WordPress에 포스트를 발행합니다.
        
        Args:
            post_data: 포스트 데이터
        
        Returns:
            생성된 포스트 정보 또는 None
        """
        import requests
        
        # 카테고리 ID 가져오기
        category_name = post_data.get('category', 'Uncategorized')
        category_slug = post_data.get('category_slug', None)
        category_id = self.get_or_create_category(category_name, category_slug)
        
        # 태그 ID 가져오기
        tag_names = post_data.get('tags', [])
        tag_ids = self.get_or_create_tags(tag_names)
        
        # 포스트 데이터 구성
        wp_post = {
            'title': post_data.get('title', ''),
            'slug': post_data.get('slug', ''),
            'content': post_data.get('content', ''),
            'excerpt': post_data.get('excerpt', ''),
            'status': 'publish',
            'categories': [category_id] if category_id else [],
            'tags': tag_ids,
            'meta': {
                'seo_title': post_data.get('title', ''),
                'seo_description': post_data.get('meta_description', '')
            }
        }
        
        # Schema.org JSON-LD 추가
        if 'schema_markup' in post_data:
            wp_post['meta']['schema_markup'] = json.dumps(post_data['schema_markup'])
        
        try:
            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=wp_post,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"포스트 발행 완료: {result['link']}")
                return {
                    'id': result['id'],
                    'url': result['link'],
                    'slug': result['slug']
                }
            else:
                logger.error(f"포스트 발행 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"포스트 발행 중 오류: {e}")
            return None

# ==============================================================================
# 발행 함수
# ==============================================================================
def publish_post(filename: str) -> Optional[Dict[str, Any]]:
    """
    지정된 파일의 포스트를 WordPress에 발행합니다.
    
    Args:
        filename: output/ 폴더의 파일명
    
    Returns:
        발행 결과 또는 None
    """
    logger.info(f"WordPress 발행 시작: {filename}")
    
    # WordPress 설정 가져오기
    wp_config = get_wordpress_config()
    
    if not wp_config['site_url'] or not wp_config['username'] or not wp_config['password']:
        logger.error("WordPress API 설정이 완료되지 않았습니다. .env 파일을 확인해주세요.")
        return None
    
    # 포스트 데이터 로드
    try:
        post_data = load_output_json(filename)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {filename}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        return None
    
    # WordPressPublisher 인스턴스 생성
    publisher = WordPressPublisher(
        site_url=wp_config['site_url'],
        username=wp_config['username'],
        password=wp_config['password']
    )
    
    # 연결 확인
    if not publisher.check_connection():
        logger.error("WordPress API 연결에 실패했습니다.")
        return None
    
    logger.info("WordPress API 연결 확인 완료")
    
    # 포스트 발행
    result = publisher.create_post(post_data)
    
    if result:
        # 발행 결과 저장
        post_data['published'] = True
        post_data['published_at'] = datetime.now().isoformat()
        post_data['published_url'] = result['url']
        post_data['wp_post_id'] = result['id']
        
        # 발행 완료 파일로 저장
        published_filename = filename.replace('.json', '_published.json')
        from common import save_json
        save_json(post_data, published_filename)
        
        logger.info(f"발행 완료 파일 저장: {published_filename}")
    
    return result

def get_latest_unpublished() -> Optional[str]:
    """
    가장 최근의 미발행 포스트 파일을 찾습니다.
    
    Returns:
        파일명 또는 None
    """
    from common import list_output_files
    
    files = list_output_files()
    published_files = [f for f in files if '_published' in f]
    published_bases = [f.replace('_published.json', '.json') for f in published_files]
    
    all_posts = [f for f in files if f.endswith('.json') and '_published' not in f and '_optimized' not in f]
    
    unpublished = [f for f in all_posts if f not in published_bases]
    
    if unpublished:
        return sorted(unpublished, reverse=True)[0]
    return None

# ==============================================================================
# 메인 함수
# ==============================================================================
def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="포스트를 WordPress에 발행합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/wp_publisher.py --file "post_20250101_abc123.json"
  python scripts/wp_publisher.py --latest
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", type=str, help="output/ 폴더의 파일명")
    group.add_argument("--latest", "-l", action="store_true", help="가장 최근 미발행 파일 자동 선택")
    
    args = parser.parse_args()
    
    # 환경변수 로드
    load_environment()
    
    # 파일 선택
    if args.file:
        filename = args.file
        if not filename.endswith(".json"):
            filename += ".json"
    else:
        filename = get_latest_unpublished()
        if not filename:
            logger.error("발행할 포스트가 없습니다.")
            sys.exit(1)
        logger.info(f"가장 최근 미발행 파일 선택: {filename}")
    
    # 발행 실행
    result = publish_post(filename)
    
    if result:
        print(f"\n{'='*60}")
        print(f"✅ WordPress 발행 완료!")
        print(f"{'='*60}")
        print(f"📄 제목: {load_output_json(filename).get('title', 'N/A')}")
        print(f"🔗 URL: {result['url']}")
        print(f"🆔 포스트 ID: {result['id']}")
        print(f"{'='*60}\n")
    else:
        print(f"\n❌ WordPress 발행에 실패했습니다.")
        print(f"   logs/wp_publisher.log를 확인해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()