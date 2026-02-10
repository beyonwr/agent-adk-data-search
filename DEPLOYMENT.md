# Production Deployment Guide

Docker 없이 Linux 서버에 Agent ADK Data Search를 배포하는 가이드입니다.

## 요구사항

### 프로덕션 서버 (Linux)
- Ubuntu 20.04+ 또는 Debian 10+ 권장
- Python 3.10 이상
- systemd (자동 실행용)
- 최소 2GB RAM 권장
- Git

### 방화벽 설정
- 8000 포트 오픈 (외부 접근 필요 시)

## 배포 방법

### 방법 1: 자동 배포 스크립트 사용 (권장)

1. **프로덕션 서버에 접속**
   ```bash
   ssh user@your-server-ip
   ```

2. **배포 스크립트 다운로드**
   ```bash
   # 프로젝트 저장소에서 deploy.sh 다운로드
   wget https://raw.githubusercontent.com/YOUR_REPO/YOUR_PROJECT/main/deploy.sh
   # 또는
   curl -O https://raw.githubusercontent.com/YOUR_REPO/YOUR_PROJECT/main/deploy.sh
   ```

3. **실행 권한 부여 및 실행**
   ```bash
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

4. **환경 변수 설정**
   - 스크립트가 `.env` 파일을 생성하면 편집하여 프로덕션 설정 입력
   ```bash
   sudo nano /opt/agent-adk-data-search/.env
   ```

5. **서비스 재시작**
   ```bash
   sudo systemctl restart adk-web
   ```

### 방법 2: 수동 배포

1. **프로덕션 서버에 접속**
   ```bash
   ssh user@your-server-ip
   ```

2. **시스템 패키지 설치**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.10 python3.10-venv python3-pip git
   ```

3. **애플리케이션 디렉토리 생성**
   ```bash
   sudo mkdir -p /opt/agent-adk-data-search
   cd /opt/agent-adk-data-search
   ```

4. **저장소 클론**
   ```bash
   sudo git clone YOUR_REPOSITORY_URL .
   ```

5. **가상 환경 생성 및 활성화**
   ```bash
   sudo python3.10 -m venv venv
   sudo venv/bin/pip install --upgrade pip
   sudo venv/bin/pip install -r requirements.txt
   ```

6. **환경 변수 설정**
   ```bash
   sudo cp env.sample .env
   sudo nano .env
   ```

   필수 설정 항목:
   - `PADO_API_KEY`: API 키
   - `PADO_MODEL_NAME`: 모델 이름
   - `PADO_MODEL_API`: API 베이스 URL
   - `TEXT_EMBEDDING_MODEL_URL`: 임베딩 모델 URL
   - `POSTGRESQL_DB_*`: PostgreSQL 데이터베이스 정보
   - `CHROMADB_HOST`, `CHROMADB_PORT`: ChromaDB 정보

7. **systemd 서비스 설치**
   ```bash
   sudo cp adk-web.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable adk-web.service
   ```

8. **권한 설정**
   ```bash
   sudo chown -R www-data:www-data /opt/agent-adk-data-search
   ```

9. **서비스 시작**
   ```bash
   sudo systemctl start adk-web.service
   ```

10. **서비스 상태 확인**
    ```bash
    sudo systemctl status adk-web.service
    ```

## 서비스 관리

### 서비스 제어
```bash
# 서비스 시작
sudo systemctl start adk-web

# 서비스 중지
sudo systemctl stop adk-web

# 서비스 재시작
sudo systemctl restart adk-web

# 서비스 상태 확인
sudo systemctl status adk-web

# 부팅 시 자동 시작 활성화
sudo systemctl enable adk-web

# 부팅 시 자동 시작 비활성화
sudo systemctl disable adk-web
```

### 로그 확인
```bash
# systemd 로그 (실시간)
sudo journalctl -u adk-web -f

# systemd 로그 (최근 100줄)
sudo journalctl -u adk-web -n 100

# 애플리케이션 로그 파일
sudo tail -f /var/log/adk-web.log
```

## 업데이트

### 코드 업데이트
```bash
cd /opt/agent-adk-data-search
sudo git pull
sudo venv/bin/pip install -r requirements.txt
sudo systemctl restart adk-web
```

### 환경 변수 업데이트
```bash
sudo nano /opt/agent-adk-data-search/.env
sudo systemctl restart adk-web
```

## 접속 확인

배포 후 다음 URL로 접속:
```
http://YOUR_SERVER_IP:8000
```

## 방화벽 설정 (필요 시)

### UFW 사용 시
```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### iptables 사용 시
```bash
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

## 문제 해결

### 서비스가 시작되지 않는 경우
1. 로그 확인
   ```bash
   sudo journalctl -u adk-web -n 50
   ```

2. 환경 변수 확인
   ```bash
   sudo cat /opt/agent-adk-data-search/.env
   ```

3. Python 의존성 확인
   ```bash
   sudo /opt/agent-adk-data-search/venv/bin/pip list
   ```

### 포트 충돌
다른 서비스가 8000 포트를 사용 중인 경우:
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 8000

# 또는
sudo lsof -i :8000
```

서비스 파일에서 포트 변경:
```bash
sudo nano /etc/systemd/system/adk-web.service
# --port 8000을 다른 포트로 변경
sudo systemctl daemon-reload
sudo systemctl restart adk-web
```

### 권한 오류
```bash
sudo chown -R www-data:www-data /opt/agent-adk-data-search
sudo chmod -R 755 /opt/agent-adk-data-search
```

## 보안 권장사항

1. **방화벽 설정**: 필요한 포트만 오픈
2. **리버스 프록시 사용**: Nginx 또는 Apache와 함께 사용 권장
3. **SSL/TLS 설정**: HTTPS 사용 권장
4. **환경 변수 보안**: `.env` 파일 권한을 600으로 설정
   ```bash
   sudo chmod 600 /opt/agent-adk-data-search/.env
   ```

## Nginx 리버스 프록시 설정 (선택사항)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Windows vs Linux 차이점

이 프로젝트는 Windows에서 개발되었지만 Linux에서도 문제없이 동작합니다:

- **경로**: Python 코드는 `os.path` 또는 `pathlib`를 사용하므로 플랫폼 독립적
- **의존성**: requirements.txt의 모든 패키지는 Linux에서도 사용 가능
- **systemd**: Windows에는 없지만 Linux에서 서비스 자동 시작을 위해 사용
- **가상 환경**: 두 플랫폼 모두 동일하게 작동

## 추가 리소스

- [systemd 공식 문서](https://systemd.io/)
- [Python venv 문서](https://docs.python.org/3/library/venv.html)
- [Nginx 문서](https://nginx.org/en/docs/)
