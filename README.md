# Agent ADK Data Search

Google Agent ADK 기반의 데이터 검색 에이전트 시스템입니다.

## 기능

- PostgreSQL 데이터베이스를 통한 데이터 검색
- ChromaDB를 활용한 벡터 검색
- 자연어 쿼리를 SQL로 변환
- 다중 에이전트 아키텍처

## 요구사항

- Python 3.10 이상
- PostgreSQL 데이터베이스
- ChromaDB 인스턴스
- LLM API (PADO 또는 호환 API)

## 로컬 개발 환경 설정

### 1. 저장소 클론
```bash
git clone YOUR_REPOSITORY_URL
cd agent-adk-data-search
```

### 2. 가상 환경 생성 및 활성화

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# Windows
copy env.sample .env

# Linux/Mac
cp env.sample .env
```

`.env` 파일을 편집하여 필요한 설정을 입력하세요.

### 5. 실행
```bash
adk web --host 0.0.0.0 --port 8000
```

## 프로덕션 배포

Docker 없이 Linux 서버에 배포하는 방법은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

### 빠른 배포

```bash
# 프로덕션 서버에서
chmod +x deploy.sh
sudo ./deploy.sh
```

자세한 내용은 [배포 가이드](DEPLOYMENT.md)를 확인하세요.

## 프로젝트 구조

```
agent-adk-data-search/
├── agents/              # 에이전트 관련 코드
│   ├── sub_agents/     # 서브 에이전트
│   ├── utils/          # 유틸리티 함수
│   ├── constants/      # 상수 정의
│   └── agent.py        # 메인 에이전트
├── deploy.sh           # 배포 스크립트
├── adk-web.service     # systemd 서비스 파일
├── requirements.txt    # Python 의존성
├── env.sample          # 환경 변수 템플릿
└── DEPLOYMENT.md       # 배포 가이드
```

## 환경 변수

주요 환경 변수는 `env.sample` 파일을 참고하세요:

- `PADO_API_KEY`: LLM API 키
- `PADO_MODEL_NAME`: 사용할 모델 이름
- `POSTGRESQL_DB_*`: PostgreSQL 연결 정보
- `CHROMADB_HOST`, `CHROMADB_PORT`: ChromaDB 연결 정보
- `TEXT_EMBEDDING_MODEL_URL`: 임베딩 모델 API URL

## 서비스 관리 (프로덕션)

```bash
# 서비스 시작
sudo systemctl start adk-web

# 서비스 중지
sudo systemctl stop adk-web

# 서비스 재시작
sudo systemctl restart adk-web

# 서비스 상태 확인
sudo systemctl status adk-web

# 로그 확인
sudo journalctl -u adk-web -f
```

## 문제 해결

로그 확인:
```bash
# systemd 로그
sudo journalctl -u adk-web -n 100

# 애플리케이션 로그
sudo tail -f /var/log/adk-web.log
```

## 라이센스

[여기에 라이센스 정보 추가]

## 기여

[여기에 기여 가이드라인 추가]
