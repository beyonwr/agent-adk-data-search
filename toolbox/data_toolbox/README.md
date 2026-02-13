# Data Toolbox

다른 팀의 DA Agent에서 사용할 수 있는 데이터 수집 도구 모음입니다. MCP 리소스 시스템을 사용하여 결과를 저장합니다.

## 기능

### 1. query_data
PostgreSQL 데이터베이스에서 SQL 쿼리를 실행하고 결과를 CSV 리소스로 저장합니다.

**파라미터:**
- `sql_query` (str): 실행할 SQL 쿼리문
- `limit` (int, optional): 반환할 최대 행 수 (기본값: 제한 없음)

**반환값:**
```python
{
    "status": "success",
    "outputs": [
        {
            "type": "resource_link",
            "uri": "mcp://resources/<job_id>.csv",
            "filename": "<job_id>.csv",
            "mime_type": "text/csv",
            "description": "SQL 쿼리 결과 | N행 × M열 | 컬럼: ...",
            "metadata": {
                "row_count": N,
                "columns": [...],
                "timestamp": "..."
            }
        }
    ]
}
```

### 2. search_similar_columns
ChromaDB 벡터 검색을 사용하여 유사한 컬럼명을 찾고 JSON 리소스로 저장합니다.

**파라미터:**
- `query_text` (str): 검색할 자연어 텍스트
- `n_results` (int, optional): 반환할 결과 개수 (기본값: 10)

**반환값:**
```python
{
    "status": "success",
    "outputs": [
        {
            "type": "resource_link",
            "uri": "mcp://resources/<job_id>.json",
            "filename": "<job_id>.json",
            "mime_type": "application/json",
            "description": "유사 컬럼 검색 결과 | 쿼리: '...' | N개 결과 | ...",
            "metadata": {
                "query": "...",
                "results_count": N
            }
        }
    ]
}
```

### 3. get_database_context
현재 설정된 데이터베이스 및 환경 변수 컨텍스트 정보를 반환합니다.

**파라미터:**
없음

**반환값:**
```python
{
    "status": "success",
    "context": {
        "postgresql": {
            "database": "your_database",
            "host": "localhost",
            "port": "5432",
            "default_table": "your_table_name",
            "note": "Use query_data() tool to execute SQL queries on this database"
        },
        "chromadb": {
            "host": "localhost",
            "port": "8000",
            "collection": "your_collection",
            "note": "Use search_similar_columns() tool to find relevant column names"
        },
        "embedding": {
            "model": "BAAI/bge-m3",
            "note": "Model used for vector similarity search in ChromaDB"
        }
    },
    "message": "Database context retrieved successfully"
}
```

**사용 목적:**
- 다른 팀의 DA Agent가 작업할 데이터베이스/테이블 정보를 확인
- 사용 가능한 ChromaDB 컬렉션 확인
- 환경 설정 확인 및 디버깅

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

data_toolbox를 사용하기 위해 다음 환경 변수들을 설정해야 합니다:

### MCP 리소스 저장 경로
```bash
export MCP_RESOURCE_ROOT="/path/to/mcp/resources"
```

### PostgreSQL
```bash
export POSTGRESQL_DB_USER="your_username"
export POSTGRESQL_DB_PASS="your_password"
export POSTGRESQL_DB_NAME="your_database"
export POSTGRESQL_DB_HOST="localhost"
export POSTGRESQL_DB_PORT="5432"
export POSTGRESQL_DB_TABLE="your_table_name"  # (Optional) 기본 테이블명
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
# - get_database_context()                             # 데이터베이스 컨텍스트 확인
# - query_data(sql_query, limit)                        # SQL 쿼리 실행
# - search_similar_columns(query_text, n_results)       # 유사 컬럼 검색

# 사용 예제:
# 1. 먼저 컨텍스트 확인
response = await agent.run("현재 연결된 데이터베이스 정보를 알려줘")
# -> get_database_context() 호출하여 DB명, 테이블명 등 확인

# 2. SQL 쿼리 실행
response = await agent.run("users 테이블에서 최근 10명의 사용자 정보를 가져와줘")
# -> query_data("SELECT * FROM users ORDER BY created_at DESC", limit=10)

# 3. 유사 컬럼 검색
response = await agent.run("'사용자 이메일'과 유사한 컬럼명을 찾아줘")
# -> search_similar_columns("사용자 이메일", n_results=10)
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
├── get_database_context.py        # 데이터베이스 컨텍스트 정보 tool
├── requirements.txt               # 필수 의존성
├── README.md                      # 사용 설명서
└── utils/
    ├── __init__.py
    └── db_clients.py              # DB 연결 헬퍼 (POOL, ChromaDB, Embedding)
```

## 주요 특징

1. **독립적인 POOL 관리**: 자체 PostgreSQL 연결 풀을 lazy initialization으로 생성 및 관리
2. **MCP 리소스 시스템**: 모든 결과를 MCP 리소스 (`mcp://resources/`) URI로 저장
3. **ToolContext 불필요**: FastMCP와 완전 호환, Pydantic 오류 없음
4. **resource_link 패턴**: bar_chart.py와 동일한 반환 형식 사용
5. **환경 변수 기반**: 모든 설정을 환경 변수로 관리
6. **Python 3.13.11 호환**: ChromaDB 1.4.0 지원

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
