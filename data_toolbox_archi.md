# Data Toolbox Architecture

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Other Team's DA Agent"
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

    subgraph "External Dependencies"
        POOL_SRC[agents/utils/database_utils.py<br/>POOL]
        PostgreSQL[(PostgreSQL<br/>Database)]
        ChromaDB[(ChromaDB<br/>Vector Store)]
        BGE[BGE-M3-KO<br/>Embedding API]
    end

    subgraph "ADK Runtime"
        State[Agent State<br/>workspace:query_results<br/>workspace:similar_columns]
        Artifacts[Artifacts Storage<br/>CSV/JSON files]
    end

    Agent -->|uses tools| Server
    Server -->|registers| QueryTool
    Server -->|registers| SearchTool

    QueryTool -->|imports| DBClients
    SearchTool -->|imports| DBClients

    DBClients -->|imports POOL| POOL_SRC
    POOL_SRC -->|connects| PostgreSQL

    DBClients -->|connects| ChromaDB
    DBClients -->|calls| BGE

    QueryTool -->|saves results| Artifacts
    QueryTool -->|stores metadata| State
    SearchTool -->|saves results| Artifacts
    SearchTool -->|stores metadata| State

    style Agent fill:#e1f5ff
    style Server fill:#fff4e1
    style QueryTool fill:#e8f5e9
    style SearchTool fill:#e8f5e9
    style DBClients fill:#f3e5f5
```

## 2. query_data Tool Flow

```mermaid
sequenceDiagram
    participant Agent as DA Agent
    participant QueryTool as query_data
    participant POOL as PostgreSQL POOL
    participant DB as PostgreSQL
    participant ADK as ADK Runtime

    Agent->>QueryTool: query_data(sql_query)

    Note over QueryTool: 1. Sanitize SQL<br/>(remove NBSP)

    QueryTool->>POOL: Get connection
    POOL->>DB: Execute SQL query
    DB-->>POOL: Return rows + columns
    POOL-->>QueryTool: records[]

    Note over QueryTool: 2. Convert to<br/>pandas DataFrame

    Note over QueryTool: 3. Generate CSV bytes<br/>(utf-8-sig encoding)

    QueryTool->>ADK: save_artifact(filename, csv_bytes)
    ADK-->>QueryTool: version

    Note over QueryTool: 4. Generate metadata<br/>(row_count, columns,<br/>dtypes, sample_rows)

    QueryTool->>ADK: state[workspace:query_results][filename] = metadata

    QueryTool-->>Agent: {status, filename, version,<br/>row_count, columns, sample_rows}
```

## 3. search_similar_columns Tool Flow

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
    ChromaClient->>ChromaDB: Get collection
    ChromaDB-->>ChromaClient: collection
    ChromaClient-->>SearchTool: collection

    SearchTool->>Embedding: POST /embeddings<br/>{input: [query_text]}
    Embedding-->>SearchTool: embeddings[]

    SearchTool->>ChromaDB: collection.query(<br/>query_embeddings,<br/>n_results)
    ChromaDB-->>SearchTool: {documents, distances,<br/>metadatas, ids}

    Note over SearchTool: Format results:<br/>combine docs + distances<br/>+ metadata + ids

    Note over SearchTool: Convert to JSON bytes<br/>(ensure_ascii=False)

    SearchTool->>ADK: save_artifact(filename, json_bytes)
    ADK-->>SearchTool: version

    Note over SearchTool: Generate metadata<br/>(query, n_results)

    SearchTool->>ADK: state[workspace:similar_columns][filename] = metadata

    SearchTool-->>Agent: {status, filename, version,<br/>query, results_count, top_results}
```

## 4. Component Details

### 4.1 FastMCP Server Registration

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

### 4.2 Database Clients Helper

```mermaid
graph TB
    subgraph "utils/db_clients.py"
        ImportPOOL[Import POOL from<br/>agents/utils/database_utils]

        ChromaFunc[get_chromadb_client]
        EmbedFunc[get_embedding]

        EnvVars[Environment Variables:<br/>CHROMADB_HOST<br/>CHROMADB_PORT<br/>CHROMADB_COLLECTION_NAME<br/>TEXT_EMBEDDING_MODEL_URL<br/>TEXT_EMBEDDING_MODEL_NAME]

        EnvVars --> ChromaFunc
        EnvVars --> EmbedFunc
    end

    style ImportPOOL fill:#e3f2fd
    style ChromaFunc fill:#f3e5f5
    style EmbedFunc fill:#f3e5f5
    style EnvVars fill:#fff9c4
```

### 4.3 State Management

```mermaid
graph TB
    subgraph "Agent State"
        QueryState["workspace:query_results<br/>{<br/>  filename: {<br/>    version, mime_type,<br/>    bytes, timestamp,<br/>    row_count, columns,<br/>    dtypes, sample_rows<br/>  }<br/>}"]

        SearchState["workspace:similar_columns<br/>{<br/>  filename: {<br/>    version, mime_type,<br/>    bytes, timestamp,<br/>    query, n_results<br/>  }<br/>}"]
    end

    style QueryState fill:#e8f5e9
    style SearchState fill:#e1f5ff
```

## 5. Data Flow Summary

### query_data:
1. **Input**: SQL query string
2. **Process**:
   - Sanitize SQL (remove NBSP)
   - Execute via PostgreSQL POOL
   - Convert to pandas DataFrame
   - Generate CSV with utf-8-sig encoding
3. **Output**:
   - CSV artifact saved to ADK
   - Metadata stored in state
   - Returns summary with sample rows

### search_similar_columns:
1. **Input**: Natural language query text
2. **Process**:
   - Get embedding from BGE-M3-KO API
   - Query ChromaDB with vector similarity
   - Combine results with metadata
   - Generate JSON with full results
3. **Output**:
   - JSON artifact saved to ADK
   - Metadata stored in state
   - Returns summary with top 3 results

## 6. Usage Example

```python
from toolbox.data_toolbox import data_toolbox
from google.adk import Agent

# Create DA agent with data_toolbox
agent = Agent(
    name="data_analysis_agent",
    tools=[data_toolbox],
    model="gemini-2.0-flash-exp",
)

# The agent can now use:
# - query_data(sql_query, artifact_filename)
# - search_similar_columns(query_text, n_results, artifact_filename)
```

## 7. Key Design Decisions

1. **POOL Reuse**: Import existing PostgreSQL connection pool to avoid duplicate connections
2. **ADK Artifacts**: Save all results as artifacts (CSV/JSON) for persistence and sharing
3. **State Metadata**: Store file metadata in agent state for tracking and discovery
4. **FastMCP Pattern**: Follow existing toolbox pattern (plot_toolbox) for consistency
5. **No Metadata Tool**: Removed get_column_metadata as metadata was reference-only
6. **All in data_toolbox**: Centralized location for easy import by other teams
