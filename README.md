# Agent ADK Data Search

Google Agent Development Kit (ADK) 기반의 자연어 → SQL 자동화 시스템

## 개요

이 프로젝트는 한국어 자연어 질의를 받아 자동으로 SQL을 생성하고 PostgreSQL 데이터베이스를 조회하는 AI 에이전트 시스템입니다.

## 기술 스택

- **프레임워크**: Google Agent Development Kit (ADK)
- **언어**: Python 3.13
- **데이터베이스**: PostgreSQL
- **벡터 DB**: ChromaDB
- **임베딩 모델**: BGE-M3-KO

## 프로젝트 구조

자세한 아키텍처는 [architecture.md](architecture.md)를 참고하세요.

---

## 🚀 Production 배포 가이드

### 사전 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- 최소 4GB RAM
- 20GB 디스크 공간

### 1. 환경 설정

```bash
# .env.production 파일 복사 및 수정
cp .env.production .env.production.local

# 필수 환경변수 설정
vi .env.production.local
```

**중요 설정 항목:**
- `PADO_API_KEY`: LLM API 키
- `PADO_MODEL_API`: LLM API 엔드포인트
- `POSTGRESQL_DB_PASS`: PostgreSQL 비밀번호 (강력한 비밀번호 사용)
- `TEXT_EMBEDDING_MODEL_URL`: 임베딩 서버 URL
- `CHROMADB_COLLECTION_NAME`: ChromaDB 컬렉션 이름

### 2. 배포 방법

#### 옵션 A: Docker Compose로 전체 스택 실행 (권장)

```bash
# 빌드 및 실행
docker-compose --env-file .env.production.local up -d

# 로그 확인
docker-compose logs -f app

# 상태 확인
docker-compose ps
```

#### 옵션 B: 개별 서비스 실행

```bash
# PostgreSQL만 실행
docker-compose up -d postgres

# ChromaDB만 실행
docker-compose up -d chromadb

# 애플리케이션 실행
docker-compose up -d app
```

### 3. 서비스 접근

- **PostgreSQL**: `localhost:5432`
- **ChromaDB**: `localhost:8000`
- **Application**: 컨테이너 내부에서 실행

### 4. 데이터 초기화

```bash
# PostgreSQL에 초기 데이터 로드 (필요시)
docker exec -i agent-adk-postgres psql -U postgres -d agent_production_db < init.sql

# ChromaDB 컬렉션 초기화 (필요시)
# 커스텀 스크립트 실행
```

### 5. 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f chromadb

# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

### 6. 백업

```bash
# PostgreSQL 백업
docker exec agent-adk-postgres pg_dump -U postgres agent_production_db > backup_$(date +%Y%m%d).sql

# ChromaDB 백업 (볼륨 복사)
docker run --rm -v agent-adk-data-search_chromadb_data:/data -v $(pwd):/backup alpine tar czf /backup/chromadb_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### 7. 업데이트

```bash
# 코드 업데이트
git pull origin main

# 컨테이너 재빌드 및 재시작
docker-compose build
docker-compose up -d

# 또는 한 번에
docker-compose up -d --build
```

### 8. 중지 및 정리

```bash
# 서비스 중지 (데이터 유지)
docker-compose stop

# 서비스 중지 및 컨테이너 제거 (데이터 유지)
docker-compose down

# 완전 삭제 (데이터 포함)
docker-compose down -v

# 이미지도 함께 삭제
docker-compose down --rmi all -v
```

---

## 🔧 고급 설정

### SSL/TLS 설정

PostgreSQL SSL 연결을 위해 `docker-compose.yml`에 인증서 볼륨 추가:

```yaml
volumes:
  - ./certs:/certs:ro
environment:
  POSTGRES_SSL_MODE: require
```

### 리소스 제한

Production 환경에서 리소스 제한 설정:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 네트워크 보안

외부 접근 차단:

```yaml
ports:
  - "127.0.0.1:5432:5432"  # localhost만 접근 가능
```

### 고가용성 (HA)

- PostgreSQL: Replication 설정
- ChromaDB: Cluster 모드 구성
- Application: 여러 인스턴스 실행 (Load Balancer 필요)

---

## 🐛 트러블슈팅

### 연결 오류

```bash
# 네트워크 확인
docker network ls
docker network inspect agent-adk-data-search_agent-network

# 컨테이너 간 통신 테스트
docker exec agent-adk-app ping postgres
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 로그 확인
docker-compose logs postgres

# 수동 연결 테스트
docker exec -it agent-adk-postgres psql -U postgres
```

### ChromaDB 문제

```bash
# ChromaDB 로그 확인
docker-compose logs chromadb

# ChromaDB 헬스체크
curl http://localhost:8000/api/v1/heartbeat
```

### 디스크 공간 부족

```bash
# Docker 디스크 사용량 확인
docker system df

# 불필요한 리소스 정리
docker system prune -a --volumes
```

---

## 📝 개발 환경

개발 환경에서 실행:

```bash
# 로컬 환경 설정
cp env.sample .env
vi .env

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
python run.py
```

---

## 📚 참고 문서

- [아키텍처 문서](architecture.md)
- [Google ADK 문서](https://github.com/google/adk)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

## 🔒 보안 주의사항

1. **절대로** `.env.production` 파일을 Git에 커밋하지 마세요
2. 프로덕션 환경에서는 강력한 비밀번호 사용
3. 정기적으로 인증 정보 로테이션
4. 방화벽 규칙 설정으로 불필요한 포트 차단
5. SSL/TLS 암호화 사용
6. 정기적인 보안 업데이트 및 패치

---

## 📄 라이선스

[프로젝트 라이선스 정보]

## 👥 기여

[기여 가이드라인]

## 📧 문의

[문의처 정보]
