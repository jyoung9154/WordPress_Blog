#!/bin/bash
# ==============================================================================
# AI 자동화 영어 금융 블로그 시스템 - 원클릭 설치 스크립트
# ==============================================================================
# 이 파일의 역할: 서버 환경 설정부터 Docker 설치, 서비스 실행까지 한 번에 처리
# 사용법: chmod +x install.sh && ./install.sh
# ==============================================================================

set -e  # 에러 발생 시 스크립트 중지

# ==============================================================================
# 색상 정의 (로그 출력용)
# ==============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# 로그 출력 함수
# ==============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# 스크립트 시작
# ==============================================================================
echo "=============================================="
echo " AI 자동화 영어 금융 블로그 시스템 설치"
echo "=============================================="
echo ""

# ==============================================================================
# 1. 시스템 업데이트
# ==============================================================================
log_info "시스템 패키지를 업데이트하는 중..."
sudo apt update -qq
sudo apt upgrade -y -qq
log_success "시스템 업데이트 완료"

# ==============================================================================
# 2. 필수 패키지 설치
# ==============================================================================
log_info "필수 패키지를 설치하는 중..."

# Docker 설치에 필요한 패키지
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    unzip \
    git \
    python3 \
    python3-pip \
    python3-venv \
    certbot \
    python3-certbot-nginx

log_success "필수 패키지 설치 완료"

# ==============================================================================
# 3. Docker 설치
# ==============================================================================
if command -v docker &> /dev/null; then
    log_warning "Docker가 이미 설치되어 있습니다"
else
    log_info "Docker를 설치하는 중..."
    
    # Docker GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker 저장소 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt update -qq
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Docker 서비스 시작
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_success "Docker 설치 완료"
fi

# ==============================================================================
# 4. Docker Compose 설치 (독립 실행형)
# ==============================================================================
if command -v docker-compose &> /dev/null; then
    log_warning "Docker Compose가 이미 설치되어 있습니다"
else
    log_info "Docker Compose를 설치하는 중..."
    
    # 최신 버전 다운로드
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 실행 권한 부여
    sudo chmod +x /usr/local/bin/docker-compose
    
    # 심볼릭 링크作成
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose 설치 완료"
fi

# ==============================================================================
# 5. 프로젝트 디렉토리 생성
# ==============================================================================
log_info "프로젝트 디렉토리를 확인하는 중..."

# 현재 디렉토리가 blog-automation인지 확인
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml 파일이 없습니다. 올바른 디렉토리에서 실행해주세요."
    exit 1
fi

# 필요한 디렉토리 생성
mkdir -p config scripts web_review/templates logs output backup/mysql nginx/conf.d nginx/ssl

log_success "디렉토리 구조 생성 완료"

# ==============================================================================
# 6. 환경변수 파일 생성
# ==============================================================================
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_info ".env.example을 .env로 복사하는 중..."
        cp .env.example .env
        log_warning ".env 파일이 생성되었습니다. .env 파일을 열어 실제 값으로 수정해주세요."
        log_warning "수정 필요: MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, API 키들"
    else
        log_error ".env.example 파일이 없습니다."
        exit 1
    fi
else
    log_warning ".env 파일이 이미 존재합니다"
fi

# ==============================================================================
# 7. Python 의존성 설치
# ==============================================================================
log_info "Python 의존성을 설치하는 중..."

# 가상환경 생성 (선택사항이지만 권장)
python3 -m venv venv
source venv/bin/activate

# requirements.txt가 없으면 생성
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
# AI API 클라이언트
anthropic>=0.18.0
openai>=1.12.0

# HTTP 요청
requests>=2.31.0
httpx>=0.26.0

# 웹 프레임워크
flask>=3.0.0
werkzeug>=3.0.0

# 데이터 처리
python-dotenv>=1.0.0
python-dateutil>=2.8.0

# 로깅
colorlog>=6.8.0

# 스케줄링
schedule>=1.2.0
EOF
    log_info "requirements.txt 파일을 생성했습니다"
fi

# 의존성 설치
pip install --upgrade pip -qq
pip install -r requirements.txt -qq

log_success "Python 의존성 설치 완료"

# ==============================================================================
# 8. Docker 컨테이너 시작
# ==============================================================================
log_info "Docker 컨테이너를 시작하는 중..."

# .env 파일 확인
if ! grep -q "여기에" .env 2>/dev/null; then
    log_info ".env 파일이 설정된 것으로 보입니다. 컨테이너를 시작합니다..."
    
    # Docker 컨테이너 시작
    docker compose up -d
    
    log_success "Docker 컨테이너 시작 완료"
else
    log_warning ".env 파일이 아직 완전히 설정되지 않았습니다"
    log_warning "아래 명령으로 수동으로 시작해주세요: docker compose up -d"
fi

# ==============================================================================
# 9. SSL 인증서 설정 (선택사항)
# ==============================================================================
read -p "Let's Encrypt SSL 인증서를 설정하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "도메인 이름을 입력하세요: " DOMAIN
    read -p "이메일 주소를 입력하세요: " EMAIL
    
    log_info "SSL 인증서를 신청하는 중..."
    sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --redirect --non-interactive
    
    log_success "SSL 인증서 설정 완료"
fi

# ==============================================================================
# 10. 설치 완료 메시지
# ==============================================================================
echo ""
echo "=============================================="
echo " 설치가 완료되었습니다!"
echo "=============================================="
echo ""
echo "다음 단계를 진행해주세요:"
echo ""
echo "1. .env 파일을 열어 모든 값을 실제 값으로 수정"
echo "2. WordPress 관리자 페이지에서 기본 설정 완료"
echo "3. AI API 키 설정 확인"
echo "4. config/topics.json 파일을編集하여 블로그 주제 설정"
echo ""
echo "서비스 접속 주소:"
echo "  - WordPress: http://localhost:8080 (또는 https://your-domain.com)"
echo "  - n8n: http://localhost:5678"
echo ""
echo "로그 확인:"
echo "  docker compose logs -f wordpress"
echo "  docker compose logs -f n8n"
echo ""
echo "=============================================="