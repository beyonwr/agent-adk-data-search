# MCP Server Tools Specification

현재 Agent가 사용하는 tool들을 MCP Server로 분리하기 위한 명세서입니다.
FastMCP를 사용하여 구현할 예정입니다.

## 1. Vector Search & Embedding Tools

### 1.1 Text Embedding Tool

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `get_text_embedding` |
| **역할 상세** | BGE-M3-KO 임베딩 모델을 사용하여 텍스트 리스트를 벡터 임베딩으로 변환합니다. 한국어 텍스트에 최적화되어 있으며, 벡터 유사도 검색의 전처리 단계로 사용됩니다. |
| **Input** | `text_list`: list[str] - 임베딩으로 변환할 텍스트 리스트 |
| **Output** | `embeddings`: list[list[float]] - 각 텍스트에 대응하는 벡터 임베딩 리스트. 각 임베딩은 고차원 float 배열입니다. |

**환경변수 요구사항:**
- `TEXT_EMBEDDING_MODEL_URL`: 임베딩 모델 API 엔드포인트
- `TEXT_EMBEDDING_MODEL_NAME`: 사용할 모델 이름 (예: bge-m3-ko)

**예시:**
```python
# Input
text_list = ["사용자 이름을 조회해줘", "최근 주문 내역"]

# Output
embeddings = [
    [0.123, -0.456, 0.789, ...],  # 첫 번째 텍스트의 임베딩 벡터
    [0.321, -0.654, 0.987, ...]   # 두 번째 텍스트의 임베딩 벡터
]
```

---

### 1.2 Similarity Search Tool

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `search_similar_documents` |
| **역할 상세** | ChromaDB 벡터 데이터베이스에서 입력 쿼리와 유사한 문서를 검색합니다. 사용자 질의와 관련된 데이터베이스 칼럼 정보나 메타데이터를 찾는 RAG(Retrieval-Augmented Generation) 시스템의 핵심 기능입니다. 내부적으로 `get_text_embedding`을 호출하여 쿼리를 임베딩으로 변환한 후 유사도 검색을 수행합니다. |
| **Input** | - `query_list`: list[str] - 검색할 쿼리 텍스트 리스트<br>- `n_results`: int (기본값: 3) - 반환할 유사 문서 개수 |
| **Output** | `documents`: list[list[str]] - 각 쿼리에 대해 유사도 순으로 정렬된 문서 리스트. 2차원 배열 형태로 반환됩니다. |

**환경변수 요구사항:**
- `CHROMADB_HOST`: ChromaDB 서버 호스트
- `CHROMADB_PORT`: ChromaDB 서버 포트 (기본값: 8000)
- `CHROMADB_COLLECTION_NAME`: 검색할 컬렉션 이름

**예시:**
```python
# Input
query_list = ["사용자 테이블의 이메일 칼럼"]
n_results = 5

# Output
documents = [
    [
        "user.email: 사용자 이메일 주소 (VARCHAR)",
        "user.username: 사용자명 (VARCHAR)",
        "user.contact_email: 연락처 이메일 (VARCHAR)",
        "customer.email: 고객 이메일 (VARCHAR)",
        "account.email: 계정 이메일 (VARCHAR)"
    ]
]
```

---

## 2. Database Tools

### 2.1 PostgreSQL Query Executor

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `execute_postgres_query` |
| **역할 상세** | PostgreSQL 데이터베이스에 대해 SQL SELECT 쿼리를 비동기로 실행하고 결과를 반환합니다. 연결 풀을 사용하여 효율적인 연결 관리를 제공하며, 쿼리 결과는 딕셔너리 형태의 레코드 리스트로 반환됩니다. CSV 형식으로 변환 가능한 구조화된 데이터를 제공합니다. |
| **Input** | `sql_query`: str - 실행할 PostgreSQL SELECT 문. 완전한 SQL 문법을 따라야 합니다. |
| **Output** | - `status`: str - "success" 또는 "error"<br>- `message`: str - 실행 결과 메시지<br>- `data`: dict - 쿼리 결과 데이터<br>&nbsp;&nbsp;- `type`: "csv_table"<br>&nbsp;&nbsp;- `content`: dict<br>&nbsp;&nbsp;&nbsp;&nbsp;- `sql`: str - 실행된 SQL 쿼리<br>&nbsp;&nbsp;&nbsp;&nbsp;- `records`: list[dict] - 결과 레코드 배열. 각 레코드는 {컬럼명: 값} 형태의 딕셔너리 |

**환경변수 요구사항:**
- `POSTGRESQL_DB_USER`: 데이터베이스 사용자명
- `POSTGRESQL_DB_PASS`: 데이터베이스 비밀번호
- `POSTGRESQL_DB_NAME`: 데이터베이스 이름
- `POSTGRESQL_DB_HOST`: 데이터베이스 호스트
- `POSTGRESQL_DB_PORT`: 데이터베이스 포트

**에러 처리:**
- SQL 문법 오류, 권한 오류, 연결 실패 등의 경우 `status: "error"`와 함께 상세 에러 메시지 반환

**예시:**
```python
# Input
sql_query = "SELECT user_id, username, email FROM users WHERE created_at > '2024-01-01' LIMIT 10"

# Output (성공)
{
    "status": "success",
    "message": "SQL executed.",
    "data": {
        "type": "csv_table",
        "content": {
            "sql": "SELECT user_id, username, email FROM users WHERE created_at > '2024-01-01' LIMIT 10",
            "records": [
                {"user_id": 1, "username": "john_doe", "email": "john@example.com"},
                {"user_id": 2, "username": "jane_smith", "email": "jane@example.com"},
                ...
            ]
        }
    }
}

# Output (에러)
{
    "status": "error",
    "message": "Error while querying DB: relation 'users' does not exist"
}
```

---

## 3. RAG Support Tools

### 3.1 SQL Reference Document Retriever

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `get_sql_reference_documents` |
| **역할 상세** | 사용자의 자연어 질의를 기반으로 SQL 생성에 필요한 참조 문서를 ChromaDB에서 검색합니다. 데이터베이스 스키마, 칼럼 설명, 예제 쿼리 등의 컨텍스트 정보를 제공하여 LLM이 더 정확한 SQL을 생성할 수 있도록 지원합니다. `search_similar_documents`를 내부적으로 활용합니다. |
| **Input** | - `user_query`: str - 사용자의 자연어 질의<br>- `n_results`: int (기본값: 15) - 검색할 참조 문서 개수 |
| **Output** | `reference_docs`: list[str] - 사용자 질의와 관련된 참조 문서 리스트 (JSON 문자열 형태). 데이터베이스 칼럼 메타데이터, 설명, 예제 등을 포함합니다. |

**예시:**
```python
# Input
user_query = "2024년 1월 이후 가입한 사용자의 이메일 주소를 알려줘"
n_results = 15

# Output
reference_docs = [
    "table: users, column: user_id, type: INTEGER, description: 고유 사용자 식별자",
    "table: users, column: email, type: VARCHAR(255), description: 사용자 이메일 주소",
    "table: users, column: created_at, type: TIMESTAMP, description: 계정 생성 일시",
    "table: users, column: username, type: VARCHAR(100), description: 사용자명",
    ...
]
```

---

## 4. State Management Tools (선택적)

### 4.1 Column Name Extraction Completer

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `complete_column_extraction` |
| **역할 상세** | 사용자 질의에서 데이터베이스 칼럼명 추출이 완료되었음을 확인하고 다음 단계(SQL 생성)로 진행할 수 있도록 신호를 보냅니다. 추출된 칼럼명이 없는 경우 에러를 반환합니다. Agent의 workflow 제어에 사용됩니다. |
| **Input** | `extracted_columns`: dict - 추출된 칼럼명 정보<br>&nbsp;&nbsp;- `items`: list[dict] - 추출된 칼럼명 리스트. 각 항목은 `{"extracted_column_name": str}` 형태 |
| **Output** | - `status`: str - "success" 또는 "error"<br>- `message`: str - 완료 메시지 또는 에러 메시지<br>- `escalate`: bool - 다음 단계로 진행 여부 (true일 경우 escalate) |

**예시:**
```python
# Input (성공 케이스)
extracted_columns = {
    "items": [
        {"extracted_column_name": "user_id"},
        {"extracted_column_name": "email"},
        {"extracted_column_name": "created_at"}
    ]
}

# Output
{
    "status": "success",
    "message": "Column name extraction completed.",
    "escalate": true
}

# Input (실패 케이스)
extracted_columns = {"items": []}

# Output
{
    "status": "error",
    "message": "Column name extraction required.",
    "escalate": false
}
```

---

## 5. Utility Tools

### 5.1 NBSP Sanitizer

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `sanitize_for_csv` |
| **역할 상세** | LLM이 생성한 텍스트에서 Non-Breaking Space(NBSP, `\u00A0`) 문자를 일반 공백으로 변환합니다. CSV/Excel 파일에 저장할 때 발생할 수 있는 인코딩 문제를 방지합니다. |
| **Input** | `text`: str - 정제할 텍스트 |
| **Output** | `sanitized_text`: str - NBSP가 제거된 텍스트 |

**예시:**
```python
# Input
text = "SELECT\u00A0user_id,\u00A0email FROM users"

# Output
sanitized_text = "SELECT user_id, email FROM users"
```

---

## 구현 우선순위

FastMCP를 사용한 구현 시 다음 순서로 진행하는 것을 권장합니다:

1. **필수 (High Priority)**
   - `get_text_embedding` (Vector Search의 기반)
   - `search_similar_documents` (RAG 시스템의 핵심)
   - `execute_postgres_query` (데이터베이스 쿼리 실행)

2. **권장 (Medium Priority)**
   - `get_sql_reference_documents` (SQL 생성 정확도 향상)

3. **선택적 (Low Priority)**
   - `complete_column_extraction` (Workflow 제어용)
   - `sanitize_for_csv` (Utility 함수)

---

## MCP Server 구조 제안

```
mcp-server/
├── server.py                    # FastMCP 서버 엔트리포인트
├── tools/
│   ├── vector_search.py        # get_text_embedding, search_similar_documents
│   ├── database.py             # execute_postgres_query
│   ├── rag.py                  # get_sql_reference_documents
│   └── utils.py                # sanitize_for_csv, complete_column_extraction
├── config/
│   └── settings.py             # 환경변수 관리
└── requirements.txt            # FastMCP, chromadb, psycopg[pool], requests 등
```

---

## 환경변수 통합

모든 tool이 필요로 하는 환경변수 목록:

```bash
# Embedding Model
TEXT_EMBEDDING_MODEL_URL=http://localhost:8080/v1/embeddings
TEXT_EMBEDDING_MODEL_NAME=bge-m3-ko

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CHROMADB_COLLECTION_NAME=column_metadata

# PostgreSQL
POSTGRESQL_DB_USER=postgres
POSTGRESQL_DB_PASS=password
POSTGRESQL_DB_NAME=bga_database
POSTGRESQL_DB_HOST=localhost
POSTGRESQL_DB_PORT=5432
```
