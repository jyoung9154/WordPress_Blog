# 🤖 AI 자동화 영어 블로그 시스템

> Oracle Cloud Server → Docker → WordPress → AI 자동 글 생성 → 검토 → 발행 → 광고/제휴 수익화

**AI/Finance/Economy/Technology 블로그를 위한 완전한 자동화 파이프라인**

## 📋 목차

- [개요](#개요)
- [시스템 아키텍처](#시스템-아키텍처)
- [빠른 시작](#빠른-시작)
- [디렉토리 구조](#디렉토리-구조)
- [스크립트 설명](#스크립트-설명)
- [LangGraph 파이프라인](#langgraph-파이프라인)
- [n8n 스타일 파이프라인 에디터](#n8n-스타일-파이프라인-에디터)
- [관리자 대시보드](#관리자-대시보드)
- [설정 가이드](#설정-가이드)
- [사용법](#사용법)
- [수익화 전략](#수익화-전략)
- [Oracle Cloud 배포](#oracle-cloud-배포)
- [도메인 연결](#도메인-연결)
- [SEO 최적화](#seo-최적화)
- [사이트맵 제출](#사이트맵-제출)

---

## 개요

이 프로젝트는 AI를 활용하여 영어 블로그(AI, Finance, Economy, Technology)를 자동 운영할 수 있는 완전한 파이프라인입니다.

### 주요 기능

- 🤖 **다중 AI 프로바이더**: Claude, OpenAI, Gemini, Groq, Ollama 지원
- 🔄 **LangGraph 파이프라인**: 노드 기반 시각적 워크플로우
- 🎨 **n8n 스타일 에디터**: 드래그앤드롭 노드 에디터 + SVG 간선 연결
- 🔍 **SEO 최적화**: 키워드 밀도, 가독성, 구조화 데이터 자동 처리
- 🔗 **제휴링크 자동 삽입**: 카테고리별 제휴 링크 자연스러운 배치
- ✅ **검토 노드**: 웹 UI로 생성된 글 검토 후 발행
- 📤 **WordPress 자동 발행**: REST API를 통한 즉시 발행
- ⏰ **스케줄러**: 주간 자동 발행 스케줄 설정
- 🎯 **확장된 카테고리**: AI & Technology, Finance & Investing, Economy & Markets, AI Skills & Prompts

### 목표

- 월 $1 이상 지속 수익화 파이프라인 구축
- 초보자도 이해할 수 있는 직관적인 구조
- 모든 코드에 한국어 주석 포함

---

## 시스템 아키텍처

```
[Oracle Server]
│
├── Docker Compose
│   ├── WordPress (포트 80/443)
│   ├── MySQL (내부 전용)
│   └── Redis (캐시)
│
└── 자동화 파이프라인 (LangGraph)
    │
    ▼
[1] 메인 키워드 입력
    │
    ▼
[2] 서브카테고리 생성 (AI)
    │
    ▼
[3] 키워드 생성 (AI)
    │
    ▼
[4] 블로그 글 작성 (AI + MCP 연동 가능)
    │
    ▼
[5] SEO 최적화
    │
    ▼
[6] 흥미도/참여도 체크
    │
    ▼
[7] 검토 노드 (사람이 확인 후 승인/거부)
    │
    ▼
[8] WordPress 발행 (REST API)
    │
    ▼
[9] 제휴링크 삽입 + 성과 추적
```

### 다중 AI 프로바이더 아키텍처

```
┌─────────────────────────────────────────┐
│           MultiAIClient                  │
├─────────────────────────────────────────┤
│  Claude │ OpenAI │ Gemini │ Groq │ Ollama│
└─────────────────────────────────────────┘
                    │
                    ▼
            config/prompts.json
            (프로바이더별 프롬프트)
```

---

## 빠른 시작

### 1. 환경 설정

```bash
# 레포 클론 (또는 파일 다운로드)
cd blog-automation

# 환경변수 설정
cp .env.example .env
nano .env # API 키, DB 비밀번호 등 입력
```

### 2. Docker 서비스 시작

```bash
# 원클릭 설치 (권장)
chmod +x install.sh
./install.sh

# 또는 Docker만 시작
docker compose up -d
```

### 3. Python 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 웹 대시보드 시작

```bash
# 메인 검토 대시보드
python web_review/app.py

# 또는 관리자 대시보드
python web_review/admin.py

# n8n 스타일 파이프라인 에디터
# http://localhost:5000/pipeline-editor
```

### 5. 첫 글 생성 테스트

```bash
# 랜덤 키워드로 글 생성
python scripts/generate_post.py --random

# 특정 키워드로 생성
python scripts/generate_post.py --keyword "how to start investing with $100"
```

---

## 디렉토리 구조

```
blog-automation/
├── docker-compose.yml          # Docker 서비스 정의
├── .env.example                # 환경변수 템플릿
├── .env                        # 실제 환경변수 (Git 무시)
├── install.sh                  # 원클릭 설치 스크립트
├── requirements.txt            # Python 의존성
├── README.md                   # 이 파일
│
├── config/                     # 설정 파일
│   ├── topics.json             # 주제/카테고리/키워드 설정
│   ├── prompts.json            # AI 프롬프트 설정
│   └── affiliates.json         # 제휴링크 설정
│
├── scripts/                    # Python 스크립트
│   ├── common.py               # 공통 유틸리티 (MultiAIClient 포함)
│   ├── generate_post.py        # AI 글 생성
│   ├── seo_optimizer.py        # SEO 최적화
│   ├── review_queue.py         # 검토 노드
│   ├── wp_publisher.py         # WordPress 발행
│   ├── affiliate_inserter.py   # 제휴링크 삽입
│   ├── scheduler.py            # 스케줄러
│   └── pipeline/               # LangGraph 파이프라인
│       ├── __init__.py
│       ├── nodes.py            # 노드 정의
│       └── graph.py            # 그래프 정의
│
├── web_review/                 # Flask 웹 앱
│   ├── app.py                  # 메인 앱 (검토 대시보드)
│   ├── admin.py                # 관리자 대시보드
│   ├── pipeline_editor.py      # n8n 스타일 파이프라인 에디터
│   └── templates/              # HTML 템플릿
│       ├── index.html          # 메인 페이지
│       ├── post.html           # 포스트 검토 페이지
│       ├── logs.html           # 검토 로그 페이지
│       ├── error.html          # 에러 페이지
│       ├── admin/              # 관리자 템플릿
│       │   ├── dashboard.html
│       │   ├── settings.html
│       │   ├── settings_ai.html
│       │   ├── settings_wordpress.html
│       │   ├── settings_categories.html
│       │   ├── posts.html
│       │   └── monitoring.html
│       └── pipeline_editor/    # 파이프라인 에디터 템플릿
│           └── index.html
│
├── logs/                       # 로그 파일 저장
│   └── (자동 생성)
│
└── output/                     # 생성된 글 저장
    └── (자동 생성)
```

---

## 스크립트 설명

### generate_post.py
AI를 사용하여 블로그 포스트를 생성합니다.

```bash
# 랜덤 키워드로 생성
python scripts/generate_post.py --random

# 특정 키워드로 생성
python scripts/generate_post.py --keyword "best index funds for beginners"

# 카테고리 내 우선순위 키워드로 생성
python scripts/generate_post.py --category "investing-beginners"
```

### seo_optimizer.py
생성된 포스트의 SEO를 최적화합니다.

```bash
# 특정 파일 최적화
python scripts/seo_optimizer.py --file "post_xxx.json"

# 가장 최근 파일 최적화
python scripts/seo_optimizer.py --latest
```

**최적화 항목:**
- 키워드 밀도 체크 (1.5~2.5%)
- H태그 구조 검증
- 가독성 점수 계산 (Flesch Reading Ease)
- 메타 태그 길이 검증
- Schema.org JSON-LD 생성
- 이미지 alt 태그 자동 생성

### review_queue.py
생성된 포스트를 검토하고 승인/거부/재생성 처리합니다.

```bash
# 터미널 UI
python scripts/review_queue.py

# 웹 UI
python scripts/review_queue.py --web
```

**작업 옵션:**
- [A] 승인 후 WordPress 발행
- [E] 편집 후 발행
- [R] 재생성 요청 (피드백 입력)
- [S] 건너뛰기
- [D] 삭제

### wp_publisher.py
검토가 완료된 포스트를 WordPress에 발행합니다.

```bash
# 특정 파일 발행
python scripts/wp_publisher.py --file "post_xxx.json"

# 가장 최근 미발행 파일 발행
python scripts/wp_publisher.py --latest
```

### affiliate_inserter.py
포스트에 제휴링크를 자동 삽입합니다.

```bash
# 특정 파일에 제휴링크 삽입
python scripts/affiliate_inserter.py --file "post_xxx.json"

# 가장 최근 파일에 삽입
python scripts/affiliate_inserter.py --latest
```

**규칙:**
- 글당 최대 3개 제휴링크
- 자연스러운 위치에만 삽입
- `rel="nofollow sponsored"` 자동 추가
- 제휴 공개 문구 자동 추가

### scheduler.py
전체 파이프라인 실행을 스케줄링합니다.

```bash
# 스케줄러 시작 (백그라운드)
python scripts/scheduler.py --start

# 한 번만 실행
python scripts/scheduler.py --run-once

# 상태 확인
python scripts/scheduler.py --status

# 대시보드
python scripts/scheduler.py --dashboard
```

---

## LangGraph 파이프라인

### 노드 구성

| 노드 | 설명 | 입력 | 출력 |
|------|------|------|------|
| `subcategory_generator` | 메인키워드 → 서브카테고리 | `main_keyword` | `subcategories` |
| `keyword_generator` | 서브카테고리 → 키워드 | `subcategories` | `keywords` |
| `blog_writer` | 키워드 → 블로그 글 | `keywords` | `generated_posts` |
| `seo_optimizer` | 글 → SEO 최적화 | `generated_posts` | `optimized_posts` |
| `engagement_checker` | 글 → 참여도 점수 | `optimized_posts` | `engagement_scores` |
| `reviewer` | 최종 검토 | `engagement_scores` | `review_results` |
| `wordpress_publisher` | WordPress 발행 | `review_results` | `published_posts` |

### 상태 정의 (PipelineState)

```python
class PipelineState(TypedDict, total=False):
    main_keyword: str           # 메인 키워드
    subcategories: list         # 생성된 서브카테고리
    keywords: list              # 생성된 키워드
    generated_posts: list       # AI가 생성한 글
    optimized_posts: list       # SEO 최적화된 글
    engagement_scores: list     # 참여도 점수
    review_results: list        # 검토 결과
    published_posts: list       # 발행된 글
    errors: list                # 에러 로그
```

### 파이프라인 실행

```python
from scripts.pipeline.graph import run_pipeline_simple, create_pipeline_graph

# 간단한 실행
result = run_pipeline_simple(
    main_keyword="AI investing",
    config={
        "ai_provider": "claude",
        "word_count": 1500,
        "seo_target_score": 80
    }
)

# LangGraph로 실행
graph = create_pipeline_graph()
app = graph.compile()
result = app.invoke({"main_keyword": "AI investing"})
```

---

## n8n 스타일 파이프라인 에디터

웹 브라우저에서 시각적으로 파이프라인을 편집하고 실행할 수 있습니다.

### 접속

```
http://localhost:5000/pipeline-editor
```

### 주요 기능

1. **노드 팔레트**: 사용 가능한 노드类型的 드래그앤드롭
2. **캔버스**: 노드 배치 및 SVG 간선으로 연결
3. **속성 패널**: 노드 설정 (AI 프로바이더, 프롬프트 등)
4. **저장/불러오기**: 파이프라인 설정 저장 및 불러오기
5. **실시간 실행**: 파이프라인 실행 및 로그 모니터링

### 노드 类型

| 类型 | 설명 | 색상 |
|------|------|------|
| `subcategory_generator` | 서브카테고리 생성 | 🔵 파란색 |
| `keyword_generator` | 키워드 생성 | 🟢 초록색 |
| `blog_writer` | 블로그 글 작성 | 🟣 보라색 |
| `seo_optimizer` | SEO 최적화 | 🟠 주황색 |
| `engagement_checker` | 참여도 체크 | 🟡 노란색 |
| `reviewer` | 검토 노드 | 🔴 빨간색 |
| `wordpress_publisher` | WordPress 발행 | ⚪ 흰색 |

### 사용 예시

```bash
# 파이프라인 에디터 시작
python web_review/pipeline_editor.py

# 브라우저에서 http://localhost:5000/pipeline-editor 접속
```

---

## 관리자 대시보드

WordPress 설정, AI 프로바이더 설정, 카테고리 관리 등을 웹 UI에서 할 수 있습니다.

### 접속

```
http://localhost:5000/admin
```

### 주요 기능

1. **대시보드**: 시스템 상태, 최근 활동 요약
2. **AI 설정**: 프로바이더 선택, API 키 관리
3. **WordPress 설정**: 사이트 URL, API 인증 정보
4. **카테고리 관리**: topics.json 편집
5. **포스트 관리**: 발행된 포스트 목록 및 통계
6. **모니터링**: 로그 확인, 에러 추적

### 사용 예시

```bash
# 관리자 대시보드 시작
python web_review/admin.py

# 브라우저에서 http://localhost:5000/admin 접속
```

---

## 설정 가이드

### .env 파일 설정

```bash
# MySQL
MYSQL_ROOT_PASSWORD=안전한_비밀번호
MYSQL_DATABASE=wordpress
MYSQL_USER=wp_user
MYSQL_PASSWORD=wp_비밀번호

# WordPress REST API
WP_SITE_URL=https://your-domain.com
WP_API_USERNAME=your_username
WP_API_PASSWORD=application_password

# AI 프로바이더 (기본값: claude)
AI_PROVIDER=claude

# Claude
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# OpenAI (선택)
OPENAI_API_KEY=sk-...

# Google Gemini (선택)
GEMINI_API_KEY=...

# Groq (선택)
GROQ_API_KEY=...

# Ollama (선택)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# 스케줄러
SCHEDULE_DAYS=mon,wed,fri
SCHEDULE_HOUR=9
SCHEDULE_MINUTE=0
```

### config/topics.json - 확장된 카테고리

```json
{
  "main_categories": [
    {
      "name": "AI & Technology",
      "slug": "ai-technology",
      "icon": "🤖",
      "description": "AI, 머신러닝, 기술 동향"
    },
    {
      "name": "Finance & Investing",
      "slug": "finance-investing",
      "icon": "💰",
      "description": "투자, 재무 계획, 부자 만들기"
    },
    {
      "name": "Economy & Markets",
      "slug": "economy-markets",
      "icon": "📊",
      "description": "거시경제, 시장 분석, 글로벌 동향"
    },
    {
      "name": "AI Skills & Prompts",
      "slug": "ai-skills-prompts",
      "icon": "🧠",
      "description": "AI 활용법, 프롬프트 엔지니어링"
    }
  ],
  "categories": [
    {
      "name": "AI Investing",
      "slug": "ai-investing",
      "main_category": "ai-technology",
      "priority": 1,
      "keywords": [
        {"keyword": "AI stock analysis", "competition": "medium", "cpc_range": "$3-8"},
        {"keyword": "artificial intelligence funds", "competition": "low", "cpc_range": "$2-5"}
      ]
    }
  ]
}
```

### config/prompts.json - AI 프롬프트 커스터마이즈

```json
{
  "subcategory_generator": {
    "claude": "당신은 블로그 콘텐츠 전략가입니다...",
    "openai": "You are a blog content strategist..."
  },
  "blog_writer": {
    "claude": "당신은 전문 블로그 작가입니다...",
    "openai": "You are a professional blog writer..."
  }
}
```

### config/affiliates.json 커스터마이즈

```json
{
  "products": {
    "Product Name": {
      "affiliate_url": "https://your.affiliate.link",
      "commission": "$10 per sale",
      "best_for": ["category-slug"]
    }
  }
}
```

---

## 사용법

### 전체 파이프라인 실행 (CLI)

```bash
# 1. 글 생성
python scripts/generate_post.py --random

# 2. SEO 최적화
python scripts/seo_optimizer.py --latest

# 3. 제휴링크 삽입
python scripts/affiliate_inserter.py --latest

# 4. 검토 후 발행
python scripts/review_queue.py --web
```

### 파이프라인 에디터로 실행 (GUI)

```bash
# 1. 에디터 시작
python web_review/pipeline_editor.py

# 2. 브라우저에서 http://localhost:5000/pipeline-editor 접속

# 3. 노드 연결 후 "실행" 버튼 클릭
```

### 자동화 파이프라인

```bash
# 스케줄러 시작 (매주 월, 수, 금 오전 9시 자동 실행)
python scripts/scheduler.py --start
```

---

## 수익화 전략

### 1단계 (0~3개월): 기반 구축
- Google AdSense 신청
- 월 $1~20 목표
- 10개 이상의 고품질 포스트 작성

### 2단계 (4~8개월): 제휴 마케팅
- ShareASale, CJ Affiliate 등 제휴 프로그램 신청
- 제휴링크 자동 삽입 완성
- 월 $50~200 목표

### 3단계 (9개월~): 고수익 전환
- 월 5만 방문자 달성 시 Mediavine 전환
- AdSense → Mediavine 교체 (단가 3~5배 상승)
- 월 $500~2000 목표

---

## 권장 제휴 프로그램

| 카테고리 | 프로그램 | 수수료 |
|---------|---------|--------|
| 투자 | M1 Finance | $100/signup |
| 투자 | Betterment | $50-100/signup |
| 투자 | Acorns | $10-20/install |
| 은퇴 | Vanguard | varies |
| 부채 | SoFi | $50-100/account |
| 세금 | TurboTax | $20-50/sale |
| 크레딧 | Credit Karma | $2-5/lead |

---

## 문제 해결

### Docker 관련 문제

```bash
# Docker 상태 확인
docker compose ps

# 로그 확인
docker compose logs wordpress

# 컨테이너 재시작
docker compose restart
```

### Python 스크립트 오류

```bash
# 로그 파일 확인
cat logs/generate_post.log
cat logs/wp_publisher.log

# 환경변수 확인
cat .env
```

### WordPress 연결 문제

1. WordPress REST API 활성화 확인
2. 애플리케이션 비밀번호 생성 확인
3. .env 파일의 WP_API_USERNAME/PASSWORD 확인

### AI 프로바이더 문제

```bash
# 사용 가능한 프로바이더 확인
python -c "from scripts.common import get_ai_client; c = get_ai_client(); print(c.get_available_providers())"

# 프로바이더 전환
python -c "from scripts.common import get_ai_client; c = get_ai_client(); c.set_provider('openai')"
```

---

## Oracle Cloud 배포

### 1. Oracle Cloud Always Free 계정 생성

1. [Oracle Cloud](https://www.oracle.com/cloud/free/) 접속
2. 무료 계정 등록 (신용카드 필요하지만 무료 티어만 사용)
3. 항상 무료 VM 인스턴스 2개 제공

### 2. VM 인스턴스 생성

```bash
# Oracle Cloud 콘솔에서:
# 1. "인스턴스 생성" 클릭
# 2. 설정:
#    - 이름: blog-server
#    - OS: Ubuntu 22.04 LTS
#    - 모양: VM.Standard.A1.Flex (Always Free)
#    - SSH 키 다운로드 (비밀번호 대신 사용)
```

### 3. 서버 접속 및 기본 설정

```bash
# SSH로 서버 접속
ssh -i ~/Downloads/ssh-key-name opc@서버IP주소

# 기본 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker opc

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 재접속
exit
ssh -i ~/Downloads/ssh-key-name opc@서버IP주소
```

### 4. 프로젝트 배포

```bash
# 서버에서 프로젝트 클론
git clone https://github.com/your-username/blog-automation.git
cd blog-automation

# 환경변수 설정
cp .env.example .env
nano .env  # API 키, 도메인 등 설정

# Docker 서비스 시작
docker compose up -d

# 상태 확인
docker compose ps
```

### 5. 방화벽 설정 (Oracle Cloud 콘솔)

```bash
# Oracle Cloud 콘솔에서:
# 1. 네트워킹 → 가상 클라우드 네트워크 → 보안 목록
# 2. 수신 규칙 추가:
#    - 포트 80 (HTTP)
#    - 포트 443 (HTTPS)
#    - 포트 22 (SSH)
```

### 6. 자동 재시작 설정

```bash
# 시스템 부팅 시 Docker 자동 시작
sudo systemctl enable docker
sudo systemctl enable docker-compose

# 서버 재부팅 테스트
sudo reboot
# 5분 후 접속하여 서비스 상태 확인
ssh -i ~/Downloads/ssh-key-name opc@서버IP주소
docker compose ps
```

---

## 도메인 연결

### 1. 도메인 구매 (예: Namecheap, GoDaddy, 가비아)

- 원하는 도메인 구매 (예: `yourblog.com`)
- 연간 약 $10~15

### 2. DNS 설정

**Namecheap 예시:**
```
# DNS 설정 페이지에서:
# Type: A Record
# Host: @ (또는 www)
# Value: 서버IP주소
# TTL: Automatic

# 추가 설정 (메일용)
# Type: MX
# Host: @
# Value: mail.yourblog.com
```

### 3. Oracle Cloud에서 도메인 검증

```bash
# 서버에서 도메인 연결 확인
nslookup yourblog.com
# Expected: Server: xxx.xxx.xxx.xxx, Address: 서버IP주소
```

### 4. SSL 인증서 설치 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d yourblog.com -d www.yourblog.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

### 5. WordPress URL 설정

```bash
# WordPress 관리자 페이지 접속
# 설정 → 일반
# WordPress 주소: https://yourblog.com
# 사이트 주소: https://yourblog.com
```

### 6. HTTPS 리다이렉트 설정

```bash
# /etc/nginx/conf.d/wordpress.conf 또는
# Docker volumes의 nginx 설정에서:

server {
    listen 80;
    server_name yourblog.com www.yourblog.com;
    return 301 https://$server_name$request_uri;
}
```

---

## SEO 최적화

### 1. WordPress SEO 플러그인 설치

**권장 플러그인:**
- Yoast SEO 또는 Rank Math
- Schema Pro (구조화 데이터)
- WP Fastest Cache (속도 최적화)

### 2. Yoast SEO 설정

```bash
# WordPress 관리자 → 플러그인 → 새로 추가
# "Yoast SEO" 검색 → 설치 → 활성화

# 설정 마법사 실행:
# 1. 사이트 유형: 블로그
# 2. 조직/개인: 개인
# 3. 소셜 프로필: 입력
# 4. 다중 언어: English만
```

### 3. 구조화 데이터 (Schema.org)

AI가 생성한 글에 자동으로 포함되는 구조화 데이터:
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": {
    "@type": "Person",
    "name": "Blog Author"
  },
  "datePublished": "2026-01-01",
  "dateModified": "2026-01-01"
}
```

### 4. 메타 태그 최적화

[`scripts/seo_optimizer.py`](scripts/seo_optimizer.py:1)에서 자동 생성:
- Title: 50-60자
- Meta Description: 150-160자
- Open Graph 태그
- Twitter Card 태그

### 5. 속도 최적화

```bash
# 이미지 최적화 플러그인 설치
# WordPress → 플러그인 → Smush 또는 ShortPixel

# 캐시 플러그인
# WP Fastest Cache 또는 W3 Total Cache

# CDN 사용 (Cloudflare 무료)
# cloudflare.com에서 무료 계정 생성
# 도메인 Nameserver를 Cloudflare로 변경
```

### 6. 핵심 SEO 체크리스트

| 항목 | 상태 | 설명 |
|------|------|------|
| SSL 인증서 | ✅ | HTTPS 활성화 |
| 사이트맵 | ✅ | 다음 섹션에서 설정 |
| robots.txt | ✅ | WordPress 기본 제공 |
| 구조화 데이터 | ✅ | AI가 자동 생성 |
| 메타 설명 | ✅ | SEO 플러그인 |
| 이미지 alt 태그 | ✅ | AI가 자동 생성 |
| 페이지 속도 | 🔄 | 캐시/CDN 최적화 |
| 모바일 최적화 | ✅ | 반응형 테마 |

---

## 사이트맵 제출

### 1. WordPress 사이트맵 활성화

**Yoast SEO 사용 시:**
```bash
# WordPress 관리자 → SEO → 검색的外观 → 일반
# 기능 탭 → XML 사이트맵 → 활성화
# https://yourblog.com/sitemap_index.xml 접속 확인
```

**Rank Math 사용 시:**
```bash
# WordPress 관리자 → Rank Math → sitemap 설정
# 자동 생성 활성화
```

### 2. Google Search Console 등록

1. [Google Search Console](https://search.google.com/search-console) 접속
2. 속성 추가 → 도메인 유형 → `yourblog.com` 입력
3. DNS 인증 완료

**DNS TXT 레코드 추가:**
```
# Namecheap DNS 설정:
# Type: TXT
# Host: @ (또는 google-site-verification)
# Value: google-site-verification=xxxxxx
```

### 3. 사이트맵 제출

```bash
# Search Console에서:
# 1. 좌측 메뉴 → 사이트맵
# 2. "sitemap_index.xml" 입력 → 제출
# 3. 상태 확인 (수락/오류)
```

### 4. Bing Webmaster Tools 등록

1. [Bing Webmaster Tools](https://www.bing.com/webmasters) 접속
2. 도메인 추가 → DNS 인증
3. 사이트맵 제출: `https://yourblog.com/sitemap_index.xml`

### 5. 자동 사이트맵 갱신

```bash
# WordPress가 새 글을 발행할 때마다 자동 갱신
# Yoast SEO 또는 Rank Math가 자동으로 처리

# 수동 확인:
curl https://yourblog.com/sitemap_index.xml
```

### 6. Search Console에서 성능 모니터링

```bash
# Search Console에서 확인:
# 1. 성능 → 평균 표시 위치, 클릭률
# 2. 색인 → 색인된 페이지 수
# 3. 개선사항 → Core Web Vitals 점수
```

---

## 라이선스

MIT License

---

## 기여

버그 리포트 및 기능 요청은 Issue로 등록해주세요.