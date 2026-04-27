# 🤖 AI 자동화 영어 금융 블로그 시스템 — 개발 요청 프롬프트

> **목적:** 오라클 서버 → Docker → WordPress → AI 자동 글 생성 → 검토 → 발행 → 광고/제휴 수익화  
> **대상:** 이 문서를 Claude / ChatGPT / Cursor 등 AI 개발 도구에 그대로 붙여넣어 사용

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [개발 요청 마스터 프롬프트](#3-개발-요청-마스터-프롬프트)
4. [시스템 프롬프트 (SEO + 유용성)](#4-시스템-프롬프트-seo--유용성)
5. [블로그 주제 & 카테고리 설정](#5-블로그-주제--카테고리-설정)
6. [파이프라인 노드 구성](#6-파이프라인-노드-구성)
7. [하네스 엔지니어링 (품질 신호 최적화)](#7-하네스-엔지니어링-품질-신호-최적화)
8. [제휴마케팅 연동 전략](#8-제휴마케팅-연동-전략)
9. [수익화 체크리스트](#9-수익화-체크리스트)

---

## 1. 프로젝트 개요

```
환경:     Oracle Cloud Server (Ubuntu)
컨테이너: Docker + Docker Compose
CMS:      WordPress (REST API 연동)
자동화:   n8n (self-hosted) 또는 Python 스크립트
AI:       Claude API (claude-sonnet) or OpenAI GPT-4o
목표:     월 $1 이상 지속 수익화 파이프라인 구축
```

---

## 2. 시스템 아키텍처

```
[Oracle Server]
│
├── Docker Compose
│   ├── WordPress (포트 80/443)
│   ├── MySQL (내부 전용)
│   ├── n8n (자동화 워크플로우)
│   └── Redis (캐시)
│
└── 자동화 파이프라인
    │
    ▼
[1] 키워드 입력 (수동 또는 스케줄)
    │
    ▼
[2] AI 글 생성 (Claude API)
    │
    ▼
[3] SEO 최적화 처리
    │
    ▼
[4] ✅ 검토 노드 (사람이 확인 후 승인/거부)
    │
    ▼
[5] WordPress 발행 (REST API)
    │
    ▼
[6] 제휴링크 삽입 + 성과 추적
```

---

## 3. 개발 요청 마스터 프롬프트

> ✅ **아래 내용을 AI 개발 도구에 그대로 붙여넣기 하세요**

---

```
당신은 시니어 풀스택 개발자입니다.
아래 요구사항에 맞춰 완전한 시스템을 처음부터 구축해주세요.

[환경]
- 서버: Oracle Cloud (Ubuntu 22.04)
- 모든 서비스는 Docker Compose로 구성
- WordPress + MySQL + n8n + Redis
- AI API: Claude (Anthropic) 우선, OpenAI 대체 지원
- 도메인 SSL: Let's Encrypt (Certbot 자동화)

[핵심 요구사항]
1. 초보자도 이해할 수 있도록 모든 코드에 한국어 주석 필수
2. 각 파일마다 상단에 "이 파일의 역할"을 주석으로 설명
3. 환경변수는 전부 .env 파일로 분리 (절대 하드코딩 금지)
4. 에러 발생 시 로그를 파일로 저장하고 콘솔에 출력
5. 각 단계마다 성공/실패 여부를 명확히 출력

[구현할 기능 목록]

## A. Docker 환경 구성
- docker-compose.yml 작성
  - wordpress: 최신 버전, 한국 타임존 설정
  - mysql: 8.0, 자동 백업 설정
  - n8n: self-hosted 자동화 툴
  - redis: 캐시용
  - nginx: 리버스 프록시 + SSL
- .env.example 파일 제공 (필요한 모든 변수 설명 포함)
- 설치 스크립트: install.sh (한 번에 실행 가능하게)

## B. 키워드 & 주제 관리 시스템
- config/topics.json 파일로 주제 관리
  - 사용자가 직접 편집 가능한 구조
  - 카테고리별 키워드 리스트
  - 카테고리별 제휴 링크 매핑
  - 우선순위 설정 가능
- config/prompts.json 파일로 프롬프트 관리
  - 시스템 프롬프트 (SEO 최적화)
  - 카테고리별 전문 프롬프트
  - 사용자 커스텀 프롬프트 추가 가능

## C. AI 글 생성 파이프라인 (Python)
- scripts/generate_post.py
  - Claude API로 글 생성
  - 아래 시스템 프롬프트 기반으로 작성 (별도 섹션 참조)
  - 생성된 글은 JSON으로 저장 (발행 전 검토용)
  - 글 구조: 제목, 메타설명, 본문(HTML), 태그, 카테고리, 추천 제휴링크
  - 생성 실패 시 재시도 로직 (최대 3회)

## D. SEO 최적화 처리
- scripts/seo_optimizer.py
  - 메타 제목/설명 자동 생성 (60자/160자 제한 준수)
  - 핵심 키워드 밀도 체크 (1.5~2.5% 유지)
  - 내부 링크 자동 삽입 (기존 발행글 참조)
  - 이미지 alt 태그 자동 생성
  - Schema.org JSON-LD 구조화 데이터 추가
  - 가독성 점수 체크 (Flesch Reading Ease 기준)
  - H1/H2/H3 구조 검증

## E. ✅ 검토 노드 (핵심)
- scripts/review_queue.py
  - 생성된 글 목록을 터미널에 보기 좋게 출력
  - 각 글에 대해 다음 옵션 제공:
    [A] 승인하여 WordPress에 발행
    [E] 편집 후 발행 (텍스트 에디터 열기)
    [R] AI에게 재생성 요청 (피드백 입력 가능)
    [S] 건너뛰기 (나중에 검토)
    [D] 삭제
  - 검토 결과 logs/review_log.json에 기록
  - 웹 UI 버전도 제공 (간단한 Flask 앱)
    - 브라우저에서 글 미리보기
    - 버튼으로 승인/거부/재생성

## F. WordPress 발행 모듈
- scripts/wp_publisher.py
  - WordPress REST API 사용
  - 승인된 글 자동 발행
  - 카테고리/태그 자동 생성
  - Featured Image 자동 생성 (Unsplash API 무료 사용)
  - 발행 후 URL 기록
  - 발행 실패 시 재시도

## G. 제휴링크 자동 삽입
- scripts/affiliate_inserter.py
  - 글 내 특정 키워드에 제휴링크 자동 삽입
  - 카테고리별 제휴링크 매핑 테이블
  - 삽입 규칙: 글당 최대 3개, 자연스러운 위치에만
  - rel="nofollow sponsored" 자동 추가 (Google 정책 준수)
  - 클릭 추적 파라미터 자동 추가

## H. 스케줄러 & 모니터링
- scripts/scheduler.py
  - 주간 발행 스케줄 설정 (예: 월수금 오전 9시)
  - 파이프라인 전체 실행 자동화
  - 발행 현황 대시보드 (터미널 출력)
  - 월간 리포트 생성 (발행수, 추정 트래픽, 제휴 클릭수)

[코딩 규칙 - 반드시 준수]
1. 모든 함수에 docstring 작성 (한국어)
2. 모든 주요 로직에 인라인 주석 (한국어)
3. 각 파일 상단에 해당 파일의 역할 설명
4. try-except로 에러 처리 필수
5. 성공/실패 로그 반드시 출력
6. 매직 넘버 사용 금지 (상수로 정의)
7. README.md에 각 파일 설명 포함

[디렉토리 구조]
blog-automation/
├── docker-compose.yml      # 전체 서비스 정의
├── .env.example            # 환경변수 템플릿
├── install.sh              # 원클릭 설치 스크립트
├── README.md               # 전체 사용 가이드
├── config/
│   ├── topics.json         # 주제/카테고리/키워드 설정
│   ├── prompts.json        # AI 프롬프트 설정
│   └── affiliates.json     # 제휴링크 설정
├── scripts/
│   ├── generate_post.py    # AI 글 생성
│   ├── seo_optimizer.py    # SEO 최적화
│   ├── review_queue.py     # 검토 노드
│   ├── wp_publisher.py     # WordPress 발행
│   ├── affiliate_inserter.py # 제휴링크 삽입
│   └── scheduler.py        # 스케줄러
├── web_review/
│   ├── app.py              # Flask 검토 UI
│   └── templates/          # HTML 템플릿
├── logs/                   # 모든 로그 저장
└── output/                 # 생성된 글 임시 저장

위 구조에 맞게 전체 코드를 작성해주세요.
먼저 docker-compose.yml과 install.sh부터 시작하고,
각 스크립트를 순서대로 작성해주세요.
```

---

## 4. 시스템 프롬프트 (SEO + 유용성)

> 📁 이 내용이 `config/prompts.json`의 `system_prompt` 기본값으로 들어갑니다

```json
{
  "system_prompt": {
    "base": "You are an expert financial content writer with 10+ years of experience in personal finance, investing, and financial planning. Your writing style is clear, trustworthy, and genuinely helpful — not generic AI filler.\n\nCORE WRITING PRINCIPLES:\n1. EXPERIENCE FIRST: Always include specific examples, real numbers, and scenarios that readers can relate to.\n2. ACTIONABLE: Every article must end with clear next steps the reader can take today.\n3. HONEST: Acknowledge limitations and risks. Never oversell or make unrealistic promises.\n4. STRUCTURED: Use H2/H3 headers, bullet points, and tables to improve scannability.\n5. DEPTH OVER LENGTH: 1,500 words of genuine insight beats 3,000 words of padding.\n\nSEO REQUIREMENTS:\n- Primary keyword in: H1 title, first 100 words, one H2, meta description\n- Secondary keywords naturally distributed (never forced)\n- Internal link opportunities noted with [INTERNAL_LINK: topic]\n- Affiliate link opportunities noted with [AFFILIATE: product_type]\n- Schema markup hints noted with [SCHEMA: type]\n\nCONTENT QUALITY SIGNALS (Google measures these via user behavior):\n- Hook in first 2 sentences: Make the reader need to keep reading\n- Zero fluff: Remove any sentence that doesn't add value\n- Unique angle: What does this article say that others don't?\n- Credibility markers: Cite data sources, regulations, official bodies\n- Readability: Short paragraphs (3-4 lines max), active voice, simple words\n\nFORMAT OUTPUT AS JSON:\n{\n  'title': 'SEO-optimized title (50-60 chars)',\n  'meta_description': 'Compelling description (150-160 chars)',\n  'slug': 'url-friendly-slug',\n  'content': 'Full HTML content',\n  'excerpt': 'Short summary (2-3 sentences)',\n  'tags': ['tag1', 'tag2'],\n  'estimated_read_time': 5,\n  'affiliate_opportunities': ['product1', 'product2'],\n  'internal_link_suggestions': ['topic1', 'topic2']\n}",

    "quality_checklist": [
      "Does the H1 contain the primary keyword?",
      "Is the intro hook compelling enough to prevent bounce?",
      "Are there at least 3 H2 sections?",
      "Does each section add unique value?",
      "Are there specific numbers/data points?",
      "Is there a clear conclusion with next steps?",
      "Are affiliate opportunities naturally integrated?",
      "Is the reading level appropriate (Grade 8-10)?",
      "Are there any generic AI phrases to remove? (e.g. 'It is worth noting', 'In conclusion', 'Certainly')",
      "Would a real financial expert be proud to have written this?"
    ]
  }
}
```

---

## 5. 블로그 주제 & 카테고리 설정

> 📁 `config/topics.json` — **직접 편집하세요**

```json
{
  "_comment": "이 파일을 직접 편집하여 블로그 주제와 키워드를 관리하세요",
  "_instructions": {
    "priority": "1=최고, 5=최저. 낮은 숫자가 먼저 작성됩니다",
    "competition": "low/medium/high — 낮을수록 초반에 노출 유리",
    "cpc_range": "예상 클릭당 광고 단가 (USD)"
  },

  "categories": [
    {
      "name": "Investing for Beginners",
      "slug": "investing-beginners",
      "priority": 1,
      "custom_prompt": "Write for someone who has never invested before. Assume zero financial knowledge. Use analogies.",
      "keywords": [
        {"keyword": "how to start investing with $100", "competition": "low", "cpc_range": "$2-5"},
        {"keyword": "best index funds for beginners", "competition": "medium", "cpc_range": "$3-8"},
        {"keyword": "ETF vs mutual fund for beginners", "competition": "low", "cpc_range": "$3-6"}
      ],
      "affiliate_products": ["M1 Finance", "Acorns", "Fidelity"]
    },
    {
      "name": "Retirement Planning",
      "slug": "retirement-planning",
      "priority": 2,
      "custom_prompt": "Focus on actionable retirement strategies. Include specific contribution limits and IRS rules. Target readers aged 25-45.",
      "keywords": [
        {"keyword": "Roth IRA vs traditional IRA 2025", "competition": "medium", "cpc_range": "$4-10"},
        {"keyword": "how much to save for retirement by age", "competition": "low", "cpc_range": "$3-7"},
        {"keyword": "401k contribution limits 2025", "competition": "medium", "cpc_range": "$3-8"}
      ],
      "affiliate_products": ["Betterment", "Vanguard", "Personal Capital"]
    },
    {
      "name": "Debt Payoff",
      "slug": "debt-payoff",
      "priority": 3,
      "custom_prompt": "Empathetic and non-judgmental tone. Practical strategies. Include debt avalanche vs snowball comparison.",
      "keywords": [
        {"keyword": "how to pay off student loans fast", "competition": "medium", "cpc_range": "$3-7"},
        {"keyword": "debt avalanche vs snowball method", "competition": "low", "cpc_range": "$2-5"}
      ],
      "affiliate_products": ["SoFi", "Earnest", "NaviRefi"]
    }
  ],

  "_add_your_categories_below": "위 형식을 복사해서 카테고리를 추가하세요"
}
```

---

## 6. 파이프라인 노드 구성

```
┌─────────────────────────────────────────────┐
│              전체 파이프라인                  │
└─────────────────────────────────────────────┘

[노드 1] 키워드 선택
  입력: topics.json
  출력: 선택된 키워드 + 카테고리 + 프롬프트
  자동화: 우선순위 기반 자동 선택 or 수동 입력

      ↓

[노드 2] AI 글 생성
  입력: 키워드 + 시스템 프롬프트 + 카테고리 프롬프트
  출력: JSON 형태의 글 (output/ 폴더에 저장)
  API: Claude claude-sonnet-4-20250514
  실패 시: 자동 재시도 3회

      ↓

[노드 3] SEO 자동 최적화
  입력: 생성된 글 JSON
  처리:
    - 키워드 밀도 체크 (1.5~2.5%)
    - 메타태그 길이 검증
    - H태그 구조 검증
    - 가독성 점수 계산
    - Schema.org JSON-LD 생성
    - 이미지 alt 태그 생성
  출력: SEO 점수 + 최적화된 글

      ↓

[노드 4] 제휴링크 삽입
  입력: 최적화된 글
  처리:
    - 카테고리 매핑 테이블 참조
    - 자연스러운 위치에 최대 3개 삽입
    - nofollow/sponsored 태그 추가
  출력: 제휴링크 포함된 글

      ↓

[노드 5] ✅ 검토 노드 (사람 개입)
  ┌─────────────────────────────────┐
  │  터미널 UI 또는 웹 브라우저 UI  │
  │                                 │
  │  📄 제목: ...                   │
  │  📊 SEO 점수: 87/100            │
  │  ⏱️  예상 읽기 시간: 6분        │
  │  🔗 제휴링크: 2개               │
  │                                 │
  │  [A] 승인 발행                  │
  │  [E] 편집 후 발행               │
  │  [R] 재생성 (피드백 입력)       │
  │  [S] 건너뛰기                   │
  │  [D] 삭제                       │
  └─────────────────────────────────┘

      ↓ (승인 시)

[노드 6] WordPress 발행
  입력: 승인된 글
  처리:
    - REST API로 발행
    - 카테고리/태그 자동 생성
    - Featured Image 자동 추가
  출력: 발행된 URL + 로그 기록

      ↓

[노드 7] 모니터링 & 리포팅
  - 발행 현황 기록
  - 월간 리포트 생성
  - 제휴 클릭 추적
```

---

## 7. 하네스 엔지니어링 (품질 신호 최적화)

> Google이 실제로 측정하는 사용자 행동 신호를 글 작성 단계에서 미리 최적화

### 7-1. 이탈률 (Bounce Rate) 최소화

```json
{
  "harness_rules": {
    "bounce_rate_prevention": {
      "hook_requirement": "첫 2문장 안에 독자가 계속 읽어야 하는 이유 제시",
      "hook_templates": [
        "Did you know that [shocking statistic]? Here's what most people get wrong about [topic].",
        "I made [mistake] for 3 years before learning this [solution]. Here's exactly what I'd do differently.",
        "The #1 question I get about [topic] is [question]. The answer might surprise you."
      ],
      "forbidden_openers": [
        "In this article, we will...",
        "Welcome to our guide on...",
        "Today we're going to talk about..."
      ]
    },

    "reading_time_optimization": {
      "target_minutes": "5-8분 (Google이 선호하는 깊이)",
      "word_count_range": "1500-2500",
      "paragraph_max_lines": 4,
      "sentence_max_words": 20
    },

    "scroll_depth_tactics": [
      "중간마다 요약 박스 삽입 (독자 재참여)",
      "숫자 리스트로 다음 내용 예고",
      "표/차트로 시각적 변화 제공",
      "FAQ 섹션으로 마무리 (관련 검색 커버)"
    ]
  }
}
```

### 7-2. 체류 시간 (Dwell Time) 증가

```json
{
  "dwell_time_tactics": {
    "content_structure": [
      "Quick Answer 박스: 글 상단에 핵심 답변 요약 (Featured Snippet 노리기)",
      "목차(Table of Contents): 독자가 원하는 섹션으로 이동 가능",
      "비교표: 텍스트보다 표로 정보 제공 시 체류시간 증가",
      "계산기/체크리스트: 인터랙티브 요소 (WordPress 플러그인 활용)"
    ],
    "e_e_a_t_signals": {
      "experience": "실제 사례, 개인 경험 추가 (AI가 생성하되 사람이 검토 시 추가)",
      "expertise": "저자 바이오 페이지 필수 (금융 자격증 or 경험 명시)",
      "authority": "외부 권위 사이트 인용 (IRS.gov, SEC.gov, Investopedia)",
      "trust": "업데이트 날짜 표시, 사실 확인 주석"
    }
  }
}
```

### 7-3. 재방문율 & 공유 유도

```json
{
  "return_visit_tactics": [
    "글 말미에 관련글 3개 추천",
    "이메일 뉴스레터 CTA 삽입",
    "연간 업데이트 예고 ('Updated every January')",
    "소셜 공유 버튼 (Pinterest는 금융 블로그에 효과적)"
  ],
  "ai_detection_avoidance": {
    "forbidden_phrases": [
      "It's worth noting that",
      "In conclusion",
      "Certainly",
      "As an AI",
      "I'd be happy to",
      "Absolutely",
      "Of course",
      "In today's world",
      "In this day and age",
      "Navigate the complex",
      "Leverage",
      "Delve into"
    ],
    "human_touch_additions": [
      "특정 연도 데이터 인용 (예: 'According to the 2024 Federal Reserve Survey...')",
      "논쟁적 관점 포함 (예: 'Some advisors disagree with this approach...')",
      "불확실성 인정 (예: 'This depends heavily on your tax situation...')",
      "구어체 섞기 (예: 'Here's the thing:', 'Let me be direct:')"
    ]
  }
}
```

---

## 8. 제휴마케팅 연동 전략

### 8-1. 추천 제휴 프로그램 (금융 블로그)

```json
{
  "affiliate_programs": {
    "investing": [
      {
        "name": "M1 Finance",
        "commission": "$100 per signup",
        "signup_url": "https://m1.com/affiliates",
        "cookie_days": 30,
        "best_for": "beginner investing articles"
      },
      {
        "name": "Acorns",
        "commission": "$10-20 per install",
        "signup_url": "https://www.acorns.com/affiliates/",
        "cookie_days": 30,
        "best_for": "micro-investing, spare change articles"
      },
      {
        "name": "Personal Capital (Empower)",
        "commission": "$50-100 per signup",
        "signup_url": "Impact Radius에서 신청",
        "cookie_days": 45,
        "best_for": "net worth tracking, retirement planning"
      }
    ],
    "credit_cards": [
      {
        "name": "Credit Karma",
        "commission": "$2-5 per lead",
        "note": "낮은 단가지만 전환율 높음",
        "network": "직접 신청"
      }
    ],
    "tax_software": [
      {
        "name": "TurboTax",
        "commission": "$20-50 per sale",
        "network": "CJ Affiliate (Commission Junction)",
        "best_for": "tax season articles (Jan-April)"
      },
      {
        "name": "H&R Block",
        "commission": "$15-30 per sale",
        "network": "Rakuten Advertising"
      }
    ],
    "networks": {
      "ShareASale": "금융 제휴 다수 보유, 신청 쉬움",
      "CJ_Affiliate": "대형 금융 브랜드 다수",
      "Impact_Radius": "핀테크 스타트업 많음",
      "Rakuten_Advertising": "전통 금융 브랜드"
    }
  }
}
```

### 8-2. 제휴링크 자동 삽입 규칙

```python
# config/affiliates.json 에 들어갈 내용
{
  "insertion_rules": {
    "max_per_post": 3,
    "placement": ["first mention of product", "comparison table", "conclusion CTA"],
    "html_template": "<a href='{affiliate_url}' rel='nofollow sponsored' target='_blank'>{anchor_text}</a>",
    "disclosure_required": true,
    "disclosure_text": "This post contains affiliate links. I may earn a commission at no extra cost to you."
  },

  "keyword_mapping": {
    "Roth IRA": {"product": "M1 Finance", "anchor": "open a Roth IRA"},
    "index fund": {"product": "Fidelity", "anchor": "start investing in index funds"},
    "tax return": {"product": "TurboTax", "anchor": "file your taxes"},
    "credit score": {"product": "Credit Karma", "anchor": "check your credit score free"}
  }
}
```

### 8-3. 수익화 순서 전략

```
초반 (0~3개월): Google AdSense 신청
  → 월 $1~20 목표 (트래픽 축적 기간)
  → 이 기간에 제휴 프로그램 신청 준비

중반 (4~8개월): 제휴마케팅 본격 시작
  → 글당 제휴링크 삽입 자동화 완성
  → 월 $50~200 목표

후반 (9개월~): Mediavine 전환 + 제휴 최적화
  → 월 5만 방문자 달성 시 AdSense → Mediavine 교체
  → 단가 3~5배 상승
  → 월 $500~2000 목표
```

---

## 9. 수익화 체크리스트

> 첫 $1 수익을 내기 위한 최소 요건

```
[ ] 서버 세팅
    [ ] Oracle 서버에 Docker 설치 완료
    [ ] docker-compose up -d 실행 성공
    [ ] WordPress 접속 확인
    [ ] SSL 인증서 적용 (https)

[ ] WordPress 기본 설정
    [ ] 퍼머링크 구조: /%postname%/ 설정
    [ ] Yoast SEO 플러그인 설치
    [ ] WP Rocket 또는 W3 Total Cache 설치
    [ ] 저자 바이오 페이지 작성
    [ ] Affiliate Disclosure 페이지 작성
    [ ] Privacy Policy 페이지 작성 (AdSense 필수)

[ ] 콘텐츠
    [ ] 첫 글 10개 발행 (AdSense 신청 최소 요건)
    [ ] 각 글 1,500단어 이상
    [ ] 고유한 Featured Image 적용
    [ ] 내부 링크 연결 완료

[ ] 수익화
    [ ] Google AdSense 신청
    [ ] 제휴 프로그램 1개 이상 신청 (ShareASale 추천)
    [ ] 첫 제휴링크 삽입 확인
    [ ] Google Search Console 등록
    [ ] Google Analytics 4 설치

[ ] 자동화 검증
    [ ] 파이프라인 테스트 실행 (처음부터 끝까지)
    [ ] 검토 노드에서 승인 → 발행 확인
    [ ] 스케줄러 작동 확인
    [ ] 로그 파일 정상 기록 확인
```

---

## 🚀 빠른 시작 명령어

```bash
# 1. 레포 클론 (AI가 생성한 코드)
git clone [your-repo] blog-automation
cd blog-automation

# 2. 환경변수 설정
cp .env.example .env
nano .env  # API 키, DB 비번 등 입력

# 3. 원클릭 설치
chmod +x install.sh
./install.sh

# 4. 첫 글 생성 테스트
python scripts/generate_post.py --keyword "how to start investing with $100"

# 5. 검토 후 발행
python scripts/review_queue.py

# 6. 스케줄러 시작 (자동화)
python scripts/scheduler.py --start
```

---

*이 문서는 AI 개발 도구에 붙여넣기 할 프롬프트입니다.*  
*`config/` 폴더의 JSON 파일들을 직접 편집하여 커스터마이즈하세요.*  
*질문이나 오류는 로그 파일(`logs/`)을 먼저 확인하세요.*
