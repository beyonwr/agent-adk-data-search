# Data Toolbox 아키텍처

## 1. 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "다른 팀의 DA Agent"
        Agent[Data Analysis Agent]
    end

    subgraph "toolbox/data_toolbox"
        Server[server.py<br/>FastMCP Server]
        QueryTool[query_data.py]
        SearchTool[search_similar_columns.py]

        subgraph "utils"
            DBClients[db_clients.py<br/>- POOL<br/>- get_chromadb_client<br/>- get_embedding]
        end
    end

    subgraph "외부 의존성"
        PostgreSQL[(PostgreSQL<br/>Database)]
        ChromaDB[(ChromaDB<br/>Vector Store)]
        BGE[BGE-M3-KO<br/>Embedding API]
    end

    subgraph "ADK Runtime"
        State[Agent State<br/>workspace:query_results<br/>workspace:similar_columns]
        Artifacts[Artifacts Storage<br/>CSV/JSON files]
    end

    Agent -->|도구 사용| Server
    Server -->|등록| QueryTool
    Server -->|등록| SearchTool

    QueryTool -->|import| DBClients
    SearchTool -->|import| DBClients

    DBClients -->|POOL 생성 및 연결| PostgreSQL
    DBClients -->|연결| ChromaDB
    DBClients -->|호출| BGE

    QueryTool -->|결과 저장| Artifacts
    QueryTool -->|메타데이터 저장| State
    SearchTool -->|결과 저장| Artifacts
    SearchTool -->|메타데이터 저장| State

    style Agent fill:#e1f5ff
    style Server fill:#fff4e1
    style QueryTool fill:#e8f5e9
    style SearchTool fill:#e8f5e9
    style DBClients fill:#f3e5f5
```

## 2. query_data Tool 흐름

```mermaid
sequenceDiagram
    participant Agent as DA Agent
    participant QueryTool as query_data
    participant POOL as PostgreSQL POOL
    participant DB as PostgreSQL
    participant ADK as ADK Runtime

    Agent->>QueryTool: query_data(sql_query)

    Note over QueryTool: 1. SQL 정제<br/>(NBSP 제거)

    QueryTool->>POOL: 연결 가져오기
    POOL->>DB: SQL 쿼리 실행
    DB-->>POOL: 행 + 컬럼 반환
    POOL-->>QueryTool: records[]

    Note over QueryTool: 2. pandas DataFrame으로<br/>변환

    Note over QueryTool: 3. CSV bytes 생성<br/>(utf-8-sig encoding)

    QueryTool->>ADK: save_artifact(filename, csv_bytes)
    ADK-->>QueryTool: version

    Note over QueryTool: 4. 메타데이터 생성<br/>(row_count, columns,<br/>dtypes, sample_rows)

    QueryTool->>ADK: state[workspace:query_results][filename] = metadata

    QueryTool-->>Agent: {status, filename, version,<br/>row_count, columns, sample_rows}
```

## 3. search_similar_columns Tool 흐름

```mermaid
sequenceDiagram
    participant Agent as DA Agent
    participant SearchTool as search_similar_columns
    participant ChromaClient as ChromaDB Client
    participant Embedding as BGE-M3-KO API
    participant ChromaDB as ChromaDB
    participant ADK as ADK Runtime

    Agent->>SearchTool: search_similar_columns(query_text, n_results)

    SearchTool->>ChromaClient: get_chromadb_client()
    ChromaClient-->>SearchTool: client

    SearchTool->>ChromaClient: get_collection(name)
    ChromaClient->>ChromaDB: 컬렉션 가져오기
    ChromaDB-->>ChromaClient: collection
    ChromaClient-->>SearchTool: collection

    SearchTool->>Embedding: POST /embeddings<br/>{input: [query_text]}
    Embedding-->>SearchTool: embeddings[]

    SearchTool->>ChromaDB: collection.query(<br/>query_embeddings,<br/>n_results)
    ChromaDB-->>SearchTool: {documents, distances,<br/>metadatas, ids}

    Note over SearchTool: 결과 포맷팅:<br/>docs + distances<br/>+ metadata + ids 결합

    Note over SearchTool: JSON bytes로 변환<br/>(ensure_ascii=False)

    SearchTool->>ADK: save_artifact(filename, json_bytes)
    ADK-->>SearchTool: version

    Note over SearchTool: 메타데이터 생성<br/>(query, n_results)

    SearchTool->>ADK: state[workspace:similar_columns][filename] = metadata

    SearchTool-->>Agent: {status, filename, version,<br/>query, results_count, top_results}
```

## 4. 컴포넌트 세부사항

### 4.1 FastMCP 서버 등록

```mermaid
graph LR
    subgraph "server.py"
        FastMCP[FastMCP<br/>name: data_toolbox]

        FastMCP -->|tool| QueryData[query_data function]
        FastMCP -->|tool| SearchSimilar[search_similar_columns function]
    end

    style FastMCP fill:#fff4e1
    style QueryData fill:#e8f5e9
    style SearchSimilar fill:#e8f5e9
```

### 4.2 Database Clients 헬퍼

```mermaid
graph TB
    subgraph "utils/db_clients.py"
        POOLCreate[POOL 생성<br/>psycopg_pool.AsyncConnectionPool]

        ChromaFunc[get_chromadb_client]
        EmbedFunc[get_embedding]

        EnvVars[환경 변수:<br/>PostgreSQL: USER, PASS, NAME, HOST, PORT<br/>ChromaDB: HOST, PORT, COLLECTION_NAME<br/>Embedding: MODEL_URL, MODEL_NAME]

        EnvVars --> POOLCreate
        EnvVars --> ChromaFunc
        EnvVars --> EmbedFunc
    end

    style POOLCreate fill:#e3f2fd
    style ChromaFunc fill:#f3e5f5
    style EmbedFunc fill:#f3e5f5
    style EnvVars fill:#fff9c4
```

### 4.3 State 관리

```mermaid
graph TB
    subgraph "Agent State"
        QueryState["workspace:query_results<br/>{<br/>  filename: {<br/>    version, mime_type,<br/>    bytes, timestamp,<br/>    row_count, columns,<br/>    dtypes, sample_rows<br/>  }<br/>}"]

        SearchState["workspace:similar_columns<br/>{<br/>  filename: {<br/>    version, mime_type,<br/>    bytes, timestamp,<br/>    query, n_results<br/>  }<br/>}"]
    end

    style QueryState fill:#e8f5e9
    style SearchState fill:#e1f5ff
```

## 5. 데이터 흐름 요약

### query_data:
1. **입력**: SQL 쿼리 문자열
2. **처리**:
   - SQL 정제 (NBSP 제거)
   - PostgreSQL POOL을 통해 실행
   - pandas DataFrame으로 변환
   - utf-8-sig 인코딩으로 CSV 생성
3. **출력**:
   - ADK에 CSV artifact 저장
   - State에 메타데이터 저장
   - 샘플 행과 함께 요약 반환

### search_similar_columns:
1. **입력**: 자연어 검색 텍스트
2. **처리**:
   - BGE-M3-KO API에서 임베딩 가져오기
   - ChromaDB에서 벡터 유사도 검색
   - 결과와 메타데이터 결합
   - 전체 결과를 JSON으로 생성
3. **출력**:
   - ADK에 JSON artifact 저장
   - State에 메타데이터 저장
   - 상위 3개 결과와 함께 요약 반환

## 6. 사용 예제

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

## 7. 주요 설계 결정사항

1. **독립적인 POOL 관리**: data_toolbox 내부에서 자체 PostgreSQL 연결 풀을 생성 및 관리
2. **ADK Artifacts**: 모든 결과를 artifact (CSV/JSON)로 저장하여 영속성과 공유 지원
3. **State 메타데이터**: 파일 메타데이터를 agent state에 저장하여 추적 및 검색 가능
4. **FastMCP 패턴**: 일관성을 위해 기존 toolbox 패턴(plot_toolbox) 따름
5. **Metadata Tool 제거**: get_column_metadata는 참고용이었으므로 제거
6. **data_toolbox 통합**: 다른 팀이 쉽게 import할 수 있도록 중앙화된 위치에 배치
7. **환경 변수 기반 설정**: PostgreSQL, ChromaDB, Embedding API 모두 환경 변수로 설정 관리
