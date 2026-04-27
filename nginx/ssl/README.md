# SSL 인증서 디렉토리

## 실제 배포 시

Let's Encrypt로 인증서를 발급하면 다음 파일들이 이 디렉토리에 생성됩니다:

```
nginx/ssl/
├── fullchain.pem   # 인증서 + 중간 인증서
├── privkey.pem     # 개인 키
└── README.md       # 이 파일
```

## 인증서 발급 명령

```bash
# Docker 컨테이너 실행 후
docker compose exec nginx /bin/sh -c "certbot certonly --webroot -w /var/www/html -d yourblog.com -d www.yourblog.com"

# 또는 standalone 모드 (nginx 중지 필요)
docker compose stop nginx
docker compose run --rm certbot certonly --standalone -d yourblog.com -d www.yourblog.com
docker compose up -d nginx
```

## 임시 SSL (개발용)

개발 시에는 아래 명령으로 자체 서명 인증서를 생성할 수 있습니다:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourblog.com"
```

⚠️ **경고**: 자체 서명 인증서는 브라우저에서 경고가 표시됩니다. 실제 운영 시에는 Let's Encrypt 인증서를 사용하세요.