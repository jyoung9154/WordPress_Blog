# 🚀 Oracle Cloud 배포 가이드

> Oracle Cloud Always Free VM에 Docker 기반 블로그 시스템을 배포하는 완전한 가이드

## 📋 목차

1. [사전 준비](#1-사전-준비)
2. [Oracle Cloud VM 설정](#2-oracle-cloud-vm-설정)
3. [서버 기본 설정](#3-서버-기본-설정)
4. [프로젝트 배포](#4-프로젝트-배포)
5. [도메인 연결](#5-도메인-연결)
6. [SSL 인증서](#6-ssl-인증서)
7. [서비스 관리](#7-서비스-관리)

---

## 1. 사전 준비

### 필요한 것
- Oracle Cloud 계정 (https://www.oracle.com/cloud/free/)
- 도메인 (선택사항, 예: yourblog.com)
- SSH 클라이언트 (터미널 또는 PuTTY)

### 로컬에서 준비할 파일
```bash
# 프로젝트 클론
git clone https://github.com/your-username/blog-automation.git
cd blog-automation

# .env 파일 생성
cp .env.example .env
nano .env  # API 키 등 설정
```

### .env 설정 예시
```bash
# 데이터베이스
MYSQL_ROOT_PASSWORD=YourSecurePassword123!
MYSQL_DATABASE=wordpress
MYSQL_USER=wp_user
MYSQL_PASSWORD=YourSecurePassword123!

# WordPress
WP_SITE_URL=https://yourblog.com
WP_API_USERNAME=admin
WP_API_PASSWORD=your_app_password

# AI (최소 하나 이상 필요)
AI_PROVIDER=claude
CLAUDE_API_KEY=sk-ant-xxxxx

# n8n
N8N_USER=admin
N8N_PASSWORD=YourN8NPassword123
N8N_HOST=yourblog.com
N8N_WEBHOOK_URL=https://yourblog.com/webhook

# 보안
SECRET_KEY=your-random-secret-key-here
```

---

## 2. Oracle Cloud VM 설정

### 2.1 인스턴스 생성

1. Oracle Cloud 콘솔 접속: https://cloud.oracle.com
2. "인스턴스" → "인스턴스 생성"

### 2.2 인스턴스 설정

```
이름: blog-server
 compartment: 기본값

 운영 체제: Ubuntu 22.04 LTS
 모양: VM.Standard.A1.Flex
 CPU: 1
 메모리: 6GB

 네트워킹:
 - 가상 클라우드 네트워크: 기본값 선택
 - 서브넷: 기본값 선택
 - 공인 IP 주소: "새 공인 IP 주소 할당" 선택

 SSH 키:
 - "秘密 키 다운로드" 클릭하여 저장
```

### 2.3 방화벽 설정 (네트워크 보안)

1. "네트워킹" → "가상 클라우드 네트워크" → 보안 목록
2. "수신 규칙 추가":
   - 소스 CIDR: 0.0.0.0/0
   - 대상 포트: 80, 443, 22
   - 설명: HTTP, HTTPS, SSH

### 2.4 포트 설정 (컴퓨트 인스턴스)

1. "컴퓨트" → "인스턴스" → 인스턴스 세부정보
2. "리소스" → "VNIC"
3. "보안 목록" → "수신 규칙 편집"

---

## 3. 서버 기본 설정

### 3.1 SSH 접속

```bash
# SSH 키 권한 설정
chmod 600 ~/Downloads/your-ssh-key.pem

# 서버 접속
ssh -i ~/Downloads/your-ssh-key.pem opc@서버공인IP
```

### 3.2 Docker 설치

```bash
# Docker 설치 스크립트 실행
curl -fsSL https://get.docker.com | sh

# Docker 권한 설정
sudo usermod -aG docker opc
sudo usermod -aG docker ubuntu

# Docker 시작 및 자동 시작 설정
sudo systemctl enable docker
sudo systemctl start docker

# Docker 버전 확인
docker --version
docker compose version
```

### 3.3 Docker Compose 설치 (없을 경우)

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 확인
docker-compose --version
```

### 3.4 기본 시스템 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 방화벽 설정 (UFW)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 시간대 설정
sudo timedatectl set-timezone Asia/Seoul
```

---

## 4. 프로젝트 배포

### 4.1 프로젝트 업로드

**방법 1: Git 클론 (권장)**
```bash
# 서버에서
cd ~
git clone https://github.com/your-username/blog-automation.git
cd blog-automation
```

**방법 2: SCP로 파일 전송**
```bash
# 로컬에서
scp -i ~/Downloads/your-ssh-key.pem -r ./blog-automation opc@서버IP:~/
```

### 4.2 환경변수 설정

```bash
cd blog-automation
cp .env.example .env
nano .env  # 모든 설정 입력
```

### 4.3 Docker 서비스 시작

```bash
# 이미지 빌드 및 컨테이너 시작
docker compose up -d --build

# 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

### 4.4 서비스 접속 확인

```bash
# WordPress (포트 8080)
curl http://localhost:8080

# 파이프라인 에디터 (포트 5002)
curl http://localhost:5002

# 관리자 대시보드 (포트 5000)
curl http://localhost:5000/admin
```

---

## 5. 도메인 연결

### 5.1 DNS 설정 (도메인 Registrar에서)

**Namecheap 예시:**
```
도메인: yourblog.com

A Record:
- Host: @ (또는 blog)
- Value: 서버공인IP
- TTL: Automatic

CNAME:
- Host: www
- Value: yourblog.com
- TTL: Automatic
```

### 5.2 DNS 전파 확인

```bash
# DNS 확인
nslookup yourblog.com
dig yourblog.com

# 웹사이트 확인
curl -I https://yourblog.com
```

---

## 6. SSL 인증서

### 6.1 Certbot 설치

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 6.2 Nginx 중지 (standalone 모드 사용 시)

```bash
docker compose stop nginx
```

### 6.3 인증서 발급

```bash
# 방법 1: Nginx 웹루트 방식 (권장)
sudo certbot --nginx -d yourblog.com -d www.yourblog.com

# 방법 2: Standalone (Nginx 중지 필요)
sudo certbot certonly --standalone -d yourblog.com -d www.yourblog.com
```

### 6.4 인증서 자동 갱신 설정

```bash
# 갱신 테스트
sudo certbot renew --dry-run

# Cron 작업 등록
sudo crontab -e
# 아래 줄 추가:
# 0 3 * * * sudo certbot renew --quiet
```

### 6.5 인증서 파일 복사

```bash
# Docker 볼륨으로 복사
sudo cp /etc/letsencrypt/live/yourblog.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourblog.com/privkey.pem nginx/ssl/

# 권한 설정
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

### 6.6 Nginx 시작

```bash
docker compose up -d nginx
```

---

## 7. 서비스 관리

### 7.1 주요 명령어

```bash
# 전체 서비스 상태
docker compose ps

# 모든 로그 보기
docker compose logs -f

# 특정 서비스 로그
docker compose logs -f wordpress
docker compose logs -f pipeline-editor

# 서비스 재시작
docker compose restart nginx

# 서비스 중지/시작
docker compose stop wordpress
docker compose start wordpress

# 전체 중지
docker compose down

# 전체 재시작
docker compose restart
```

### 7.2 서비스 URLs

| 서비스 | URL | 설명 |
|--------|-----|------|
| WordPress | https://yourblog.com | 메인 블로그 |
| 관리자 대시보드 | https://yourblog.com/admin | 시스템 설정 |
| 파이프라인 에디터 | https://yourblog.com/pipeline-editor | 노드 편집 |
| n8n | https://yourblog.com:5678 | 오토메이션 |

### 7.3 자동 재시작 설정

```bash
# 시스템 부팅 시 자동 시작
sudo systemctl enable docker
sudo systemctl enable docker-compose

# 서버 재부팅 테스트
sudo reboot
# 5분 후 접속하여 확인
ssh -i ~/Downloads/your-ssh-key.pem opc@서버IP
docker compose ps
```

### 7.4 백업

```bash
# WordPress 데이터 백업
docker compose exec wordpress tar -czf /backup/wordpress_backup.tar.gz -C /var/www/html .

# MySQL 데이터 백업
docker compose exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD wordpress > backup/wordpress_db.sql

# Docker 볼륨 백업
docker run --rm -v blog-automation_wordpress_data:/data -v $(pwd)/backup:/backup alpine tar -czf /backup/wordpress_volume.tar.gz -C /data .
```

### 7.5 업데이트

```bash
# Git Pull
git pull origin main

# 이미지 재빌드
docker compose up -d --build

# 불필요한 이미지 정리
docker image prune -f
```

---

## 문제 해결

### Docker 관련

```bash
# Docker 상태 확인
sudo systemctl status docker

# Docker 로그
sudo journalctl -u docker -f

# 컨테이너 내부 접속
docker exec -it blog_wordpress /bin/bash
docker exec -it blog_mysql mysql -u root -p
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
sudo netstat -tlnp | grep -E '80|443|8080|5000|5002|5678'

# 프로세스 종료
sudo kill -9 $(sudo lsof -t -i:80)
```

### SSL 인증서 문제

```bash
# 인증서 상태 확인
sudo certbot certificates

# 인증서 삭제 후 재발급
sudo certbot delete --cert-name yourblog.com
sudo certbot certonly --nginx -d yourblog.com -d www.yourblog.com
```

---

## 보안 체크리스트

- [ ] SSH 키 사용 (비밀번호 인증 비활성화)
- [ ] .env 파일을 Git에 올리지 않음
- [ ] MySQL 비밀번호 복잡하게 설정
- [ ] SSL/TLS 사용 (HTTPS)
- [ ] 방화벽 설정 (불필요한 포트 닫기)
- [ ] 정기적인 시스템 업데이트
- [ ] Docker 이미지 최신 상태 유지