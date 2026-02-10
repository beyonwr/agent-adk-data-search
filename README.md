# Agent ADK Data Search

자연어 질의를 SQL로 변환하여 데이터베이스를 조회하는 AI 에이전트 시스템입니다.

## 주요 특징

- **Google Agent Development Kit (ADK)** 기반 에이전트 시스템
- **FastMCP** 통합으로 Tool 구현 중앙화 및 MCP 프로토콜 지원
- **RAG (Retrieval-Augmented Generation)** 기반 SQL 생성
- **반복 정제 (Iterative Refinement)** 패턴을 통한 정확도 향상
- ChromaDB를 활용한 벡터 유사도 검색
- PostgreSQL 비동기 쿼리 실행

## 아키텍처

전체 시스템 아키텍처는 [architecture.md](architecture.md)를 참조하세요.

### 에이전트 구조

```
Root Agent
└── Data Search Agent (Sequential)
    ├── Column Extraction Loop (max 3 iterations)
    │   ├── Column Name Extractor
    │   └── Column Name Reviewer
    └── SQL Generation Loop (max 3 iterations)
        ├── SQL Generator (with RAG)
        └── SQL Reviewer
```

### FastMCP 통합

모든 Tool 구현은 `agents/mcp_server.py`에 FastMCP를 사용하여 중앙화되어 있습니다:

- **exit_column_extraction_loop**: 컬럼 추출 완료 신호
- **query_bga_database**: PostgreSQL 데이터베이스 쿼리 실행
- **get_sim_search**: ChromaDB 벡터 유사도 검색
- **get_sql_query_references**: RAG를 위한 참조 문서 검색

**직접 사용 패턴**: `data_search_agent.py`가 `mcp_server`를 직접 import하여 Tool을 사용합니다. 별도의 래퍼 파일 없이 필요한 곳에서 경량 인라인 어댑터로 ADK ToolContext를 처리합니다.

Tool들은 다음 두 가지 방식으로 사용 가능합니다:
1. **ADK Tool로 사용**: `mcp_server`를 직접 import하여 인라인 어댑터로 호출 (현재 방식)
2. **MCP 서버로 실행**: 독립 실행형 MCP 서버로 외부 클라이언트에 노출

## 설치

### 요구 사항

- Python 3.13+
- PostgreSQL 데이터베이스
- ChromaDB 서버
- BGE-M3-KO 임베딩 모델 서버

### 설치 단계

1. 저장소 클론:
```bash
git clone <repository-url>
cd agent-adk-data-search
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정:
```bash
cp env.sample .env
# .env 파일을 편집하여 필요한 설정 입력
```

## 환경 변수

`.env` 파일에 다음 환경 변수를 설정해야 합니다:

```bash
# LLM 설정
ROOT_AGENT_MODEL=your-model-name
ROOT_AGENT_API_BASE=https://your-api-endpoint
PADO_API_KEY=your-api-key

# PostgreSQL 설정
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DB_NAME=your_database
POSTGRESQL_DB_TABLE=your_table
POSTGRESQL_USER=your_user
POSTGRESQL_PASSWORD=your_password

# ChromaDB 설정
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
CHROMADB_COLLECTION_NAME=your_collection

# 임베딩 모델 설정
TEXT_EMBEDDING_MODEL_URL=http://localhost:8001/embeddings
TEXT_EMBEDDING_MODEL_NAME=bge-m3-ko
```

## 사용법

### ADK 에이전트로 사용

```python
from agents import root_agent

# 에이전트 실행
result = root_agent.run("2024년 1월의 매출 데이터를 보여줘")
print(result)
```

### FastMCP 서버로 실행

독립 실행형 MCP 서버로 실행하여 외부 클라이언트가 Tool을 사용할 수 있도록 합니다:

```bash
python -m agents.mcp_server
```

MCP 서버가 실행되면 다음 Tool들이 노출됩니다:
- `exit_column_extraction_loop`
- `query_bga_database`
- `get_sim_search`
- `get_sql_query_references`

## 프로젝트 구조

```
agent-adk-data-search/
├── agents/
│   ├── agent.py                 # Root Agent
│   ├── mcp_server.py           # FastMCP 서버 (모든 Tool 구현)
│   ├── constants/              # 상수 정의
│   ├── custom_types/           # 데이터 모델 (Pydantic)
│   ├── utils/                  # 유틸리티 함수들
│   └── sub_agents/
│       └── data_search_agent/
│           ├── data_search_agent.py  # Data Search Agent (인라인 Tool 어댑터 포함)
│           └── tools/
│               └── final_dict_raffello_metadata.json  # DB 메타데이터
├── requirements.txt
├── env.sample
├── README.md
└── architecture.md
```

## 개발

### Tool 추가하기

새로운 Tool을 추가하려면:

1. `agents/mcp_server.py`에 FastMCP 데코레이터를 사용하여 Tool 구현:

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int) -> dict:
    """Tool description"""
    # Implementation
    return {"status": "success", "data": result}
```

2. `data_search_agent.py`에서 직접 import하여 사용:

```python
from agents import mcp_server

def your_new_tool_adapter(param1: str, param2: int, tool_context: ToolContext):
    """Lightweight ADK adapter for FastMCP tool"""
    result = mcp_server.your_new_tool(param1, param2)
    # Handle tool_context and convert result
    return ToolResponse(
        status=result.get("status"),
        message=result.get("message")
    ).to_json()
```

3. 에이전트 정의의 `tools` 리스트에 어댑터 함수 등록

## 기여

기여는 환영합니다! Pull Request를 제출하기 전에 다음을 확인해주세요:

1. 코드가 기존 스타일을 따르는지 확인
2. 적절한 docstring 추가
3. 새로운 기능에 대한 테스트 추가

## 라이선스

[라이선스 정보]

## 문의

문의사항이 있으시면 이슈를 등록해주세요.
