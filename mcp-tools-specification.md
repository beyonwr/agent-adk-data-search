# MCP Server Tools Specification

현재 Agent가 사용하는 tool들을 MCP Server로 분리하기 위한 명세서입니다.
**실제 코드 분석 기반**으로 작성되었으며, FastMCP를 사용하여 구현할 예정입니다.

> **분석 대상 코드:**
> - `agents/sub_agents/data_search_agent/tools/bga_column_name_processor.py`
> - `agents/sub_agents/data_search_agent/tools/sql_generator_tools.py`
> - `agents/sub_agents/data_search_agent/tools/column_name_extraction_tools.py`

---

## 1. Vector Embedding Tools

### 1.1 Text Embedding Generator

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `get_text_embedding` |
| **소스 코드** | `bga_column_name_processor.py:15` - `_get_embedding()` |
| **역할 상세** | BGE-M3-KO 임베딩 모델 API를 호출하여 텍스트 리스트를 벡터 임베딩으로 변환합니다. requests 라이브러리를 사용하여 HTTP POST 요청을 보내고, 응답에서 embedding 데이터를 추출합니다. |
| **Input** | `text_list`: list[str] - 임베딩으로 변환할 텍스트 문자열 리스트 |
| **Output** | list[list[float]] - 각 입력 텍스트에 대응하는 임베딩 벡터 리스트. 각 벡터는 float 배열입니다. |

**구현 세부사항:**
```python
# 실제 구현 (bga_column_name_processor.py:15-29)
def _get_embedding(text_list: list[str]) -> list[list[float]]:
    response = requests.post(
        TEXT_EMBEDDING_MODEL_URL,
        json={"input": text_list, "model": TEXT_EMBEDDING_MODEL_NAME},
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    res_data = response.json()["data"]
    embeddings = list(map(lambda data: data["embedding"], res_data))
    return embeddings
```

**환경변수:**
- `TEXT_EMBEDDING_MODEL_URL`: 임베딩 모델 API 엔드포인트 (예: http://localhost:8080/v1/embeddings)
- `TEXT_EMBEDDING_MODEL_NAME`: 사용할 모델 이름 (예: bge-m3-ko)

**예외 처리:**
- HTTP 오류 시 `requests.HTTPError` 발생 (response.raise_for_status())

---

### 1.2 ChromaDB Similarity Search

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `get_sim_search` |
| **소스 코드** | `bga_column_name_processor.py:31` - `get_sim_search()` |
| **역할 상세** | ChromaDB HttpClient를 사용하여 벡터 유사도 검색을 수행합니다. 입력 쿼리를 임베딩으로 변환한 후(`_get_embedding` 호출), 지정된 collection에서 가장 유사한 문서를 검색합니다. RAG 시스템의 핵심 검색 엔진입니다. |
| **Input** | - `query_list`: list[str] - 검색할 쿼리 텍스트 리스트<br>- `n_results`: int = 3 (기본값) - 각 쿼리당 반환할 문서 개수 |
| **Output** | list[list[str]] - 2차원 리스트. 각 쿼리에 대해 유사도 순으로 정렬된 문서 문자열 리스트를 반환. `query_res["documents"]`를 그대로 반환합니다. |

**구현 세부사항:**
```python
# 실제 구현 (bga_column_name_processor.py:31-44)
def get_sim_search(query_list: list[str], n_results: int=3):
    chroma_client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        settings=chromadb.config.Settings(allow_reset=True, anonymized_telemetry=False)
    )
    collection = chroma_client.get_collection(CHROMADB_COLLECTION_NAME)
    embeddings = _get_embedding(query_list)
    query_res = collection.query(query_embeddings=embeddings, n_results=n_results)
    return query_res["documents"]  # list[list[str]]
```

**환경변수:**
- `CHROMADB_HOST`: ChromaDB 서버 호스트
- `CHROMADB_PORT`: ChromaDB 서버 포트 (기본값: 8000)
- `CHROMADB_COLLECTION_NAME`: 검색할 컬렉션 이름

**의존성:**
- 내부적으로 `_get_embedding()` 함수를 호출
- chromadb 라이브러리 필요

**예시:**
```python
# Input
query_list = ["사용자 이메일 칼럼", "주문 날짜 필드"]
n_results = 3

# Output
[
    [  # 첫 번째 쿼리 결과
        "users.email VARCHAR(255) 사용자 이메일 주소",
        "customers.contact_email VARCHAR(255) 고객 연락처",
        "accounts.user_email VARCHAR(255) 계정 이메일"
    ],
    [  # 두 번째 쿼리 결과
        "orders.order_date TIMESTAMP 주문 생성 일시",
        "orders.created_at TIMESTAMP 레코드 생성 시간",
        "shipments.ship_date DATE 발송 날짜"
    ]
]
```

---

## 2. Database Query Tools

### 2.1 PostgreSQL Async Query Executor

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `query_bga_database` |
| **소스 코드** | `sql_generator_tools.py:25` - `query_bga_database()` |
| **역할 상세** | psycopg AsyncConnectionPool을 사용하여 PostgreSQL 데이터베이스에 SELECT 쿼리를 비동기로 실행합니다. 쿼리 결과는 컬럼명을 키로 하는 딕셔너리 리스트 형태로 반환되며, ToolResponse 포맷으로 래핑됩니다. NBSP 문자를 자동으로 제거합니다. |
| **Input** | `generated_sql`: str - 실행할 PostgreSQL SQL 문 (완전한 쿼리) |
| **Output** | dict (JSON 형태) - ToolResponse.to_json() 결과<br>- `status`: "success" \| "error"<br>- `message`: str - 실행 메시지<br>- `data`: dict (성공 시만)<br>&nbsp;&nbsp;- `type`: "csv_table"<br>&nbsp;&nbsp;- `content`: dict<br>&nbsp;&nbsp;&nbsp;&nbsp;- `sql`: str - 실행된 SQL<br>&nbsp;&nbsp;&nbsp;&nbsp;- `records`: list[dict] - 각 row를 {컬럼명: 값} dict로 변환한 리스트 |

**구현 세부사항:**
```python
# 실제 구현 (sql_generator_tools.py:25-59)
async def query_bga_database(generated_sql: str, tool_context: ToolContext):
    generated_sql = _serialize_for_cell(generated_sql)  # NBSP 제거
    res = []

    async with POOL.connection() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(query=generated_sql)
                raw_res = await cur.fetchall()
                columns = [item.name for item in cur.description]
                res = [{k: v for k, v in zip(columns, row)} for row in raw_res]
            except Exception as e:
                return ToolResponse(
                    status="error",
                    message=f"Error while querying DB: {e}"
                ).to_json()

    return ToolResponse(
        status="success",
        message="SQL executed.",
        data=ToolResponseData(
            type="csv_table",
            content={"sql": generated_sql, "records": res}
        ).to_json(),
    ).to_json()
```

**환경변수:**
- `POSTGRESQL_DB_USER`: DB 사용자명
- `POSTGRESQL_DB_PASS`: DB 비밀번호
- `POSTGRESQL_DB_NAME`: DB 이름
- `POSTGRESQL_DB_HOST`: DB 호스트
- `POSTGRESQL_DB_PORT`: DB 포트

**연결 풀 설정 (database_utils.py:30-34):**
```python
POOL = psycopg_pool.AsyncConnectionPool(
    conninfo,
    min_size=5,
    max_size=20,
)
```

**의존성:**
- psycopg[pool] 라이브러리
- 전역 변수 `POOL` (AsyncConnectionPool)
- `_serialize_for_cell()` 유틸리티 함수

**예시:**
```python
# Input
generated_sql = "SELECT user_id, username, email FROM users LIMIT 3"

# Output (성공)
{
    "status": "success",
    "message": "SQL executed.",
    "data": {
        "type": "csv_table",
        "content": {
            "sql": "SELECT user_id, username, email FROM users LIMIT 3",
            "records": [
                {"user_id": 101, "username": "alice", "email": "alice@example.com"},
                {"user_id": 102, "username": "bob", "email": "bob@example.com"},
                {"user_id": 103, "username": "charlie", "email": "charlie@example.com"}
            ]
        }
    }
}

# Output (에러)
{
    "status": "error",
    "message": "Error while querying DB: syntax error at or near \"SELEC\""
}
```

---

## 3. Utility Tools

### 3.1 NBSP Sanitizer

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `serialize_for_cell` |
| **소스 코드** | `sql_generator_tools.py:16` - `_serialize_for_cell()` |
| **역할 상세** | LLM이 생성한 SQL이나 텍스트에서 Non-Breaking Space(`\u00A0`) 문자를 일반 공백으로 치환합니다. CSV/Excel 저장 시 인코딩 문제를 방지하기 위해 사용됩니다. |
| **Input** | `data`: str - 정제할 텍스트 문자열 |
| **Output** | str - NBSP가 제거된 텍스트 |

**구현 세부사항:**
```python
# 실제 구현 (sql_generator_tools.py:16-23)
def _serialize_for_cell(data):
    # NBSP 제거 (LLM 출력 보호)
    s = data.replace("\u00A0", " ")
    return s
```

**예시:**
```python
# Input
data = "SELECT\u00A0user_id,\u00A0email\u00A0FROM users"

# Output
"SELECT user_id, email FROM users"
```

---

## 4. MCP 분리가 어려운 Tool (참고용)

아래 tool들은 Google ADK Framework의 context와 강하게 결합되어 있어, MCP로 단순 분리하기 어렵습니다.

### 4.1 Column Extraction Loop Exit (ADK 결합)

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `exit_column_extraction_loop` |
| **소스 코드** | `column_name_extraction_tools.py:8` |
| **역할 상세** | LoopAgent의 반복 종료를 제어하는 tool입니다. `tool_context.state`에서 추출된 칼럼명을 확인하고, `tool_context.actions.escalate = True`로 설정하여 다음 단계로 진행합니다. |
| **Input** | `tool_context`: ToolContext (ADK 프레임워크 객체) |
| **Output** | dict - ToolResponse.to_json() 결과 |
| **MCP 분리 불가 이유** | - `ToolContext`는 ADK 프레임워크의 핵심 객체로, MCP에서 사용 불가<br>- `tool_context.actions.escalate`는 ADK의 workflow 제어 메커니즘<br>- `tool_context.state`는 ADK의 상태 관리 시스템 |

**실제 구현:**
```python
# column_name_extraction_tools.py:8-19
def exit_column_extraction_loop(tool_context: ToolContext):
    curr_column_names = tool_context.state.get(COLUMN_NAMES_STATES, {"items": []})

    if len(curr_column_names["items"]) == 0:
        return ToolResponse(status="error", message="Column name extraction required.").to_json()

    tool_context.actions.escalate = True  # ADK workflow 제어
    return ToolResponse(status="success", message="Column name extraction completed.").to_json()
```

---

### 4.2 SQL Reference Callback (Lifecycle Hook)

| 항목 | 내용 |
|------|------|
| **Tool 이름** | `get_sql_query_references_before_model_callback` |
| **소스 코드** | `sql_generator_tools.py:62` |
| **역할 상세** | LLM 호출 전에 실행되는 `before_model_callback`입니다. 사용자 입력에서 쿼리를 추출하고, ChromaDB에서 참조 문서를 검색하여 `llm_request.contents`에 주입합니다. RAG 시스템의 핵심이지만, callback hook이므로 일반 tool과는 다릅니다. |
| **Input** | - `callback_context`: CallbackContext (ADK 객체)<br>- `llm_request`: LlmRequest (ADK 객체) |
| **Output** | None (void) - `llm_request`를 직접 수정 |
| **MCP 분리 방식** | 이 callback의 핵심 로직인 `get_sim_search([user_input], n_results=15)[0]` 부분만 분리 가능. 전체 callback은 ADK agent에 남겨두고, 검색 기능만 MCP tool로 제공. |

**실제 구현:**
```python
# sql_generator_tools.py:62-82
def get_sql_query_references_before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
):
    user_input = callback_context.user_content.parts[0].text
    docs = get_sim_search([user_input], n_results=15)[0]  # ← 이 부분만 MCP 분리 가능
    docs_json = json.dumps(docs, ensure_ascii=False)

    # ADK state에 저장
    callback_context.state[COLUMN_NAMES_REF_DOCS_STATES] = docs_json

    # LLM request에 context 주입
    context_contents = Content(
        parts=[Part(text=f"Retrieved docs relevant to user query: {docs_json}")],
        role="user",
    )
    llm_request.contents.append(context_contents)
    return
```

---

## 5. 구현 우선순위

실제 코드 분석 결과를 바탕으로 한 FastMCP 구현 우선순위:

### 필수 구현 (High Priority)

| Tool | 이유 | MCP 분리 난이도 |
|------|------|-----------------|
| `get_text_embedding` | Vector search의 기반, 독립적인 HTTP API 호출 | ⭐ 쉬움 |
| `get_sim_search` | RAG 시스템의 핵심, ChromaDB 검색 엔진 | ⭐ 쉬움 |
| `query_bga_database` | 데이터베이스 쿼리 실행, 비즈니스 로직의 핵심 | ⭐⭐ 보통 (async pool 관리 필요) |

### 권장 구현 (Medium Priority)

| Tool | 이유 | MCP 분리 난이도 |
|------|------|-----------------|
| `serialize_for_cell` | SQL/텍스트 정제 유틸리티, 독립적 | ⭐ 쉬움 |

### 구현 불필요 (Not Recommended)

| Tool | 이유 |
|------|------|
| `exit_column_extraction_loop` | ADK workflow에 강하게 결합, MCP 분리 불가능 |
| `get_sql_query_references_before_model_callback` | Lifecycle hook, ADK agent에 남겨두어야 함 |

---

## 6. MCP Server 구조 제안

실제 코드 구조를 반영한 FastMCP 서버:

```
mcp-server/
├── pyproject.toml              # FastMCP 프로젝트 설정
├── requirements.txt            # 의존성: fastmcp, chromadb, psycopg[pool], requests
├── .env.example                # 환경변수 템플릿
├── README.md                   # MCP 서버 사용 가이드
│
├── src/
│   ├── __init__.py
│   ├── server.py               # FastMCP 서버 엔트리포인트
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── embedding.py        # get_text_embedding 구현
│   │   ├── vector_search.py    # get_sim_search 구현
│   │   ├── database.py         # query_bga_database 구현
│   │   └── utils.py            # serialize_for_cell 구현
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # 환경변수 로딩 (pydantic-settings)
│   │
│   └── models/
│       ├── __init__.py
│       └── responses.py        # ToolResponse, ToolResponseData 모델
│
└── tests/
    ├── test_embedding.py
    ├── test_vector_search.py
    └── test_database.py
```

### server.py 예시 구조

```python
from fastmcp import FastMCP
from src.tools import embedding, vector_search, database, utils

mcp = FastMCP("BGA Data Search Tools")

# Tool 등록
@mcp.tool()
def get_text_embedding(text_list: list[str]) -> list[list[float]]:
    """BGE-M3-KO 임베딩 생성"""
    return embedding.get_embedding(text_list)

@mcp.tool()
def get_sim_search(query_list: list[str], n_results: int = 3) -> list[list[str]]:
    """ChromaDB 유사도 검색"""
    return vector_search.similarity_search(query_list, n_results)

@mcp.tool()
async def query_bga_database(generated_sql: str) -> dict:
    """PostgreSQL 비동기 쿼리 실행"""
    return await database.execute_query(generated_sql)

@mcp.tool()
def serialize_for_cell(data: str) -> str:
    """NBSP 문자 제거"""
    return utils.sanitize_nbsp(data)
```

---

## 7. 환경변수 통합

실제 코드에서 사용하는 환경변수 목록:

```bash
# Text Embedding Model (bga_column_name_processor.py:11-12)
TEXT_EMBEDDING_MODEL_URL=http://localhost:8080/v1/embeddings
TEXT_EMBEDDING_MODEL_NAME=bge-m3-ko

# ChromaDB (bga_column_name_processor.py:8-10)
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CHROMADB_COLLECTION_NAME=column_metadata

# PostgreSQL (database_utils.py:10-14)
POSTGRESQL_DB_USER=postgres
POSTGRESQL_DB_PASS=password
POSTGRESQL_DB_NAME=bga_database
POSTGRESQL_DB_HOST=localhost
POSTGRESQL_DB_PORT=5432
```

---

## 8. 의존성 패키지

```txt
# requirements.txt
fastmcp>=0.1.0
chromadb>=0.4.0
psycopg[pool]>=3.1.0
requests>=2.31.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

---

## 9. MCP Tool 명세 요약표

| Tool 이름 | 소스 파일 | 함수명 | MCP 분리 | 우선순위 |
|-----------|----------|--------|---------|---------|
| `get_text_embedding` | bga_column_name_processor.py | `_get_embedding()` | ✅ 가능 | High |
| `get_sim_search` | bga_column_name_processor.py | `get_sim_search()` | ✅ 가능 | High |
| `query_bga_database` | sql_generator_tools.py | `query_bga_database()` | ✅ 가능 (ToolContext 제거 필요) | High |
| `serialize_for_cell` | sql_generator_tools.py | `_serialize_for_cell()` | ✅ 가능 | Medium |
| `exit_column_extraction_loop` | column_name_extraction_tools.py | `exit_column_extraction_loop()` | ❌ 불가능 (ADK 결합) | N/A |
| `get_sql_query_references_*` | sql_generator_tools.py | `get_sql_query_references_*()` | ⚠️ 부분 분리 (callback은 남김) | N/A |
