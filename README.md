# Agent ADK Data Search

AI 에이전트 기반 데이터 검색 시스템

## 프로젝트 개요

이 프로젝트는 Google ADK를 활용한 AI 에이전트 시스템으로, PostgreSQL과 ChromaDB를 통해 데이터를 검색하고 분석합니다.

## 요구사항

- Python 3.11+
- PostgreSQL
- ChromaDB
- Docker & Docker Compose (프로덕션 배포용)

## 로컬 개발 환경 설정

### 1. 환경 변수 설정

```bash
cp env.sample .env
# .env 파일을 열어 실제 값으로 수정
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 개발 서버 실행

```bash
adk web --host 0.0.0.0 --port 8000
```

서버가 http://localhost:8000 에서 실행됩니다.

## Docker를 이용한 프로덕션 배포 (WSL2/Linux)

### 사전 준비

1. **Docker 및 Docker Compose 설치 확인**

```bash
docker --version
docker-compose --version
```

2. **환경 변수 파일 생성**

프로젝트 루트에 `.env` 파일 생성:

```bash
cp env.sample .env
```

`.env` 파일을 열어 실제 프로덕션 환경의 값으로 수정합니다.

### 배포 방법

#### 옵션 1: Docker Compose 사용 (권장)

```bash
# 이미지 빌드 및 컨테이너 시작
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 컨테이너 상태 확인
docker-compose ps

# 중지
docker-compose down

# 재시작
docker-compose restart
```

#### 옵션 2: Docker만 사용

```bash
# 이미지 빌드
docker build -t agent-adk-data-search .

# 컨테이너 실행 (환경 변수 파일 사용)
docker run -d \
  --name agent-adk-data-search \
  --restart always \
  -p 8000:8000 \
  --env-file .env \
  agent-adk-data-search

# 로그 확인
docker logs -f agent-adk-data-search

# 중지
docker stop agent-adk-data-search

# 시작
docker start agent-adk-data-search
```

### 자동 시작 설정

Docker Compose를 사용하면 `restart: always` 옵션으로 다음과 같이 동작합니다:
- 컨테이너가 실패하면 자동으로 재시작
- 서버 재부팅 시 자동으로 시작

### WSL2에서 Docker 자동 시작 설정

WSL2에서 Windows 부팅 시 Docker를 자동으로 시작하려면:

1. **Windows Task Scheduler를 사용한 방법**

`start-docker-wsl.bat` 파일 생성:
```batch
wsl -d Ubuntu -u root service docker start
wsl -d Ubuntu -u root docker-compose -f /path/to/agent-adk-data-search/docker-compose.yml up -d
```

Task Scheduler에서 Windows 시작 시 이 배치 파일을 실행하도록 설정합니다.

2. **WSL2 systemd 사용 (Ubuntu 22.04+)**

`/etc/wsl.conf` 파일에 systemd 활성화:
```ini
[boot]
systemd=true
```

WSL 재시작 후 Docker가 systemd로 관리되어 자동 시작됩니다.

### 배포 확인

```bash
# 헬스체크
curl http://localhost:8000

# 또는 외부에서 접근 (서버 IP 사용)
curl http://your-server-ip:8000
```

### 업데이트 방법

```bash
# 코드 업데이트
git pull

# 컨테이너 재빌드 및 재시작
docker-compose up -d --build
```

### 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f

# 리소스 사용량 확인
docker stats agent-adk-data-search
```

## 트러블슈팅

### 포트가 이미 사용 중일 때

```bash
# 8000 포트를 사용 중인 프로세스 확인
sudo lsof -i :8000

# 또는 docker-compose.yml에서 포트 변경
ports:
  - "8080:8000"  # 호스트:컨테이너
```

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs

# 환경 변수 확인
docker-compose config
```

### 데이터베이스 연결 실패

- `.env` 파일의 데이터베이스 설정 확인
- PostgreSQL 및 ChromaDB가 네트워크에서 접근 가능한지 확인
- Docker 네트워크 내에서 호스트 접근 시 `host.docker.internal` 사용 (Windows/Mac)
- Linux에서는 `172.17.0.1` (Docker 브리지 IP) 또는 실제 호스트 IP 사용

## 아키텍처

자세한 아키텍처 정보는 [architecture.md](architecture.md)를 참조하세요.

## 환경 변수

주요 환경 변수 설명은 `env.sample` 파일을 참조하세요.

## 라이선스

[라이선스 정보 추가]
