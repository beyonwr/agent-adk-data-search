# Data Toolbox

다른 팀의 DA Agent에서 사용할 수 있는 데이터 수집 도구 모음입니다.

## 기능

### 1. query_data
PostgreSQL 데이터베이스에서 SQL 쿼리를 실행하고 결과를 CSV artifact로 저장합니다.

**파라미터:**
- `sql_query` (str): 실행할 SQL 쿼리문
- `artifact_filename` (str, optional): 저장할 파일명 (기본값: `query_result_YYYYMMDD_HHMMSS.csv`)

**반환값:**
- `status`: 성공/실패 상태
- `filename`: 저장된 artifact 파일명
- `version`: artifact 버전
- `row_count`: 결과 행 개수
- `columns`: 컬럼 목록
- `sample_rows`: 샘플 행 (최대 10개)

### 2. search_similar_columns
ChromaDB 벡터 검색을 사용하여 유사한 컬럼명을 찾습니다.

**파라미터:**
- `query_text` (str): 검색할 자연어 텍스트
- `n_results` (int, optional): 반환할 결과 개수 (기본값: 10)
- `artifact_filename` (str, optional): 저장할 파일명 (기본값: `similar_columns_YYYYMMDD_HHMMSS.json`)

**반환값:**
- `status`: 성공/실패 상태
- `filename`: 저장된 artifact 파일명
- `version`: artifact 버전
- `query`: 검색 쿼리
- `results_count`: 전체 결과 개수
- `top_results`: 상위 3개 결과

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

data_toolbox를 사용하기 위해 다음 환경 변수들을 설정해야 합니다:

### PostgreSQL
```bash
export POSTGRESQL_DB_USER="your_username"
export POSTGRESQL_DB_PASS="your_password"
export POSTGRESQL_DB_NAME="your_database"
export POSTGRESQL_DB_HOST="localhost"
export POSTGRESQL_DB_PORT="5432"
```

### ChromaDB
```bash
export CHROMADB_HOST="localhost"
export CHROMADB_PORT="8000"
export CHROMADB_COLLECTION_NAME="your_collection"
```

### Embedding API (BGE-M3-KO)
```bash
export TEXT_EMBEDDING_MODEL_URL="http://your-embedding-api/v1/embeddings"
export TEXT_EMBEDDING_MODEL_NAME="BAAI/bge-m3"
```

## 사용 예제

```python
from toolbox.data_toolbox import data_toolbox
from google.adk import Agent

# data_toolbox를 사용하는 DA agent 생성
agent = Agent(
    name="data_analysis_agent",
    tools=[data_toolbox],
    model="gemini-2.0-flash-exp",
)

# agent는 이제 다음 도구들을 사용할 수 있습니다:
# - query_data(sql_query, artifact_filename)
# - search_similar_columns(query_text, n_results, artifact_filename)
```

## 아키텍처

자세한 아키텍처 설명은 [data_toolbox_archi.md](../../data_toolbox_archi.md)를 참고하세요.

## 디렉토리 구조

```
toolbox/data_toolbox/
├── __init__.py                    # data_toolbox export
├── server.py                      # FastMCP 서버 등록
├── query_data.py                  # PostgreSQL 쿼리 실행 tool
├── search_similar_columns.py      # ChromaDB 벡터 검색 tool
├── requirements.txt               # 필수 의존성
├── README.md                      # 사용 설명서
└── utils/
    ├── __init__.py
    └── db_clients.py              # DB 연결 헬퍼 (POOL, ChromaDB, Embedding)
```

## 주요 특징

1. **독립적인 POOL 관리**: 자체 PostgreSQL 연결 풀을 생성 및 관리
2. **ADK Artifacts**: 모든 결과를 artifact로 저장하여 영속성 보장
3. **State 메타데이터**: agent state에 파일 메타데이터 저장
4. **FastMCP 패턴**: 기존 toolbox 패턴 준수
5. **환경 변수 기반**: 모든 설정을 환경 변수로 관리

## 문제 해결

### POOL 연결 오류
- 환경 변수가 올바르게 설정되었는지 확인
- PostgreSQL 서버가 실행 중인지 확인
- 네트워크 연결 및 방화벽 설정 확인

### ChromaDB 연결 오류
- ChromaDB 서버가 실행 중인지 확인
- `CHROMADB_HOST`와 `CHROMADB_PORT` 확인
- 컬렉션명이 올바른지 확인

### Embedding API 오류
- Embedding API 서버가 실행 중인지 확인
- `TEXT_EMBEDDING_MODEL_URL` 확인
- API 엔드포인트 형식 확인 (`/v1/embeddings`)
