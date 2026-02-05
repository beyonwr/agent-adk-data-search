---
marp: true
theme: default
paginate: true
backgroundColor: #fff
style: |
  section {
    font-family: 'Noto Sans KR', 'Arial', sans-serif;
    font-size: 24px;
  }
  h1 {
    color: #1a73e8;
    font-size: 36px;
  }
  h2 {
    color: #1a73e8;
    font-size: 30px;
  }
  code {
    font-size: 18px;
  }
  table {
    font-size: 20px;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
---

<!-- _class: lead -->
# Google Agent Development Kit (ADK)
## & Data Search Agent 프로젝트 소개

**팀 내부 기술 공유**

---

# 목차

### Part 1. Google Agent Development Kit (ADK)
1. ADK 개요 및 배경
2. 핵심 개념 (Agent, Tool, Callback)
3. Multi-Agent 시스템 아키텍처
4. 주요 기능 및 개발자 도구
5. 배포 및 에코시스템

### Part 2. Data Search Agent 프로젝트
6. 프로젝트 개요 및 목적
7. 디렉토리 구조
8. Agent 구성 및 실행 흐름
9. 핵심 도구(Tools) 및 유틸리티
10. 상태 관리 및 데이터 모델

---

<!-- _class: lead -->
# Part 1
## Google Agent Development Kit (ADK)

---

# 1. ADK 개요 및 배경

## ADK란?

Google이 **Cloud NEXT 2025**에서 발표한 **오픈소스 AI 에이전트 개발 프레임워크**

> "에이전트 개발을 소프트웨어 개발처럼 느끼게 만들자"

## 핵심 특징

- **모델 비종속적 (Model-agnostic)**: Gemini에 최적화되어 있지만, LiteLLM을 통해 다양한 LLM 사용 가능
- **배포 비종속적 (Deployment-agnostic)**: 로컬, 컨테이너, Cloud Run, Vertex AI 등 어디든 배포 가능
- **프레임워크 호환**: LangChain, CrewAI, LlamaIndex 등과 통합 가능
- **실제 Google 제품에서 사용**: Agentspace, Customer Engagement Suite(CES) 등

## 지원 언어

| Python | TypeScript | Go | Java |
|--------|------------|-----|------|
| `google-adk` v1.23+ | 공식 지원 | 공식 지원 | 공식 지원 |

---

# 2. 핵심 개념: Agent, Tool, Callback

## Agent (에이전트)

에이전트는 **특정 작업을 수행하는 기본 단위**

| 유형 | 클래스 | 설명 |
|------|--------|------|
| **LLM Agent** | `LlmAgent` | LLM 기반 추론 수행, 자연어 이해 및 의사결정 |
| **Sequential Agent** | `SequentialAgent` | 하위 에이전트를 순서대로 실행 |
| **Loop Agent** | `LoopAgent` | 조건 충족까지 반복 실행 |
| **Parallel Agent** | `ParallelAgent` | 하위 에이전트를 병렬로 실행 |

## Tool (도구)

에이전트에게 **대화 외의 능력**을 부여 (API 호출, DB 쿼리, 코드 실행 등)

## Callback (콜백)

에이전트 실행의 **특정 시점에 실행되는 커스텀 코드**

- `before_agent_callback` / `after_agent_callback`
- `before_model_callback` / `after_model_callback`
- `before_tool_callback` / `after_tool_callback`

---

# 3. Multi-Agent 시스템 아키텍처

## 이벤트 기반 런타임 (Event-Driven Runtime)

LLM을 단순 요청-응답 시스템이 아닌, **에이전트 · 도구 · 상태를 오케스트레이션**하는 구조

```
                    ┌─────────────┐
                    │  Root Agent │  (오케스트레이터)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Agent A  │ │ Agent B  │ │ Agent C  │
        │ (LLM)   │ │(Sequential)│ │ (Loop)   │
        └──────────┘ └────┬─────┘ └──────────┘
                          │
                    ┌─────┼─────┐
                    ▼           ▼
              ┌──────────┐ ┌──────────┐
              │ Sub B-1  │ │ Sub B-2  │
              └──────────┘ └──────────┘
```

## 에이전트 간 통신 방식

- **LLM 기반 전달 (Transfer)**: LLM이 판단하여 하위 에이전트에 위임
- **AgentTool 호출**: 에이전트를 도구처럼 명시적으로 호출
- **A2A 프로토콜**: 원격 에이전트 간 통신 (Agent-to-Agent Protocol)

---

# 4. 주요 기능 및 개발자 도구

## 주요 기능

| 기능 | 설명 |
|------|------|
| **Rich Tool Ecosystem** | 사전 빌트인 도구, MCP 도구, 서드파티 프레임워크 통합 |
| **Streaming** | 텍스트/오디오 양방향 실시간 스트리밍 지원 |
| **State & Memory** | 단기 대화 메모리(Session) + 장기 메모리(Memory Service) |
| **Evaluation** | 멀티턴 평가 데이터셋 생성 및 로컬 평가 도구 제공 |

## 개발자 도구

### CLI (Command Line Interface)
```bash
adk run my_agent        # 에이전트 실행
adk eval my_agent       # 에이전트 평가
```

### Developer UI
- 에이전트 실행 및 디버깅을 위한 **웹 기반 시각화 도구**
- 실행 스텝, 이벤트, 상태 변화 인스펙션 가능
- 에이전트 정의 시각화

---

# 5. 배포 및 에코시스템

## 배포 옵션

```
┌────────────────────────────────────────────────────┐
│              ADK Agent Application                 │
├────────────┬────────────┬────────────┬─────────────┤
│   Local    │ Container  │ Cloud Run  │  Vertex AI  │
│  Machine   │  (Docker)  │(Serverless)│Agent Engine │
└────────────┴────────────┴────────────┴─────────────┘
```

- **Vertex AI Agent Engine Runtime**: Google Cloud 완전 관리형 서비스 (권장)
- **Cloud Run**: 서버리스 컨테이너 배포
- **Docker 컨테이너**: 온프레미스 / 클라우드 자유 배포

## 모델 에코시스템 (LiteLLM 통합)

| Provider | 모델 예시 |
|----------|----------|
| Google | Gemini Pro, Gemini Flash |
| Anthropic | Claude Opus, Sonnet |
| OpenAI | GPT-4o, GPT-4 |
| Meta | Llama 3 |
| Mistral | Mistral Large |

> LiteLLM을 통해 100개 이상의 LLM 제공자 모델 사용 가능

---

<!-- _class: lead -->
# Part 2
## Data Search Agent 프로젝트

---

# 6. 프로젝트 개요 및 목적

## 프로젝트 목적

> **자연어로 데이터베이스를 검색하는 Multi-Agent 시스템**

사용자가 한국어로 질문하면, AI 에이전트가 자동으로:
1. 질문에서 **컬럼명을 추출**하고
2. 실제 DB 스키마에 **매핑(표준화)** 한 뒤
3. **SQL을 생성 · 검증 · 실행**하여
4. 결과를 **CSV 파일로 반환**합니다

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | Google ADK (`google-adk`) |
| 언어 | Python 3.12 |
| LLM | LiteLLM (환경변수로 모델 지정) |
| 데이터베이스 | PostgreSQL (비동기 `psycopg`) |
| 벡터 DB | ChromaDB (컬럼 설명 유사도 검색) |
| 임베딩 모델 | BGE-M3-KO (한국어 특화) |
| 데이터 검증 | Pydantic |

---

# 7. 디렉토리 구조

```
agent-adk-data-search/
├── agents/
│   ├── agent.py                          # Root Agent 정의
│   ├── prompt.yaml                       # Root Agent 프롬프트
│   │
│   ├── constants/
│   │   └── constants.py                  # 상태 키, 상수 정의
│   │
│   ├── custom_types/
│   │   ├── data_state.py                 # Pydantic 상태 모델
│   │   └── tool_response.py              # 도구 응답 스키마
│   │
│   ├── sub_agents/
│   │   └── data_search_agent/
│   │       ├── data_search_agent.py      # SequentialAgent 정의
│   │       ├── prompt.yaml               # 서브 에이전트 프롬프트
│   │       └── tools/
│   │           ├── column_name_extraction_tools.py  # 컬럼 추출 도구
│   │           ├── sql_generator_tools.py           # SQL 생성/실행 도구
│   │           ├── bga_column_name_processor.py     # 벡터 DB 검색
│   │           └── layer_info_column_description.json  # 컬럼 참조 데이터
│   │
│   └── utils/
│       ├── prompt_utils.py               # YAML 프롬프트 로딩
│       ├── database_utils.py             # DB 커넥션 풀
│       ├── file_utils.py                 # 아티팩트 저장/콜백
│       └── state_manager_utils.py        # 상태 관리 유틸리티
```

---

# 8. Agent 구성 및 실행 흐름

## 전체 실행 흐름

```
사용자 질문 (한국어)
    │
    ▼
┌─────────────────────────────────────────┐
│  Root Agent (오케스트레이터)               │
│  - 모델: LiteLLM                         │
│  - 콜백: 이미지 아티팩트 저장,             │
│          비텍스트 데이터 제거              │
└──────────────┬──────────────────────────┘
               ▼
┌─────────────────────────────────────────┐
│  Data Search Agent (SequentialAgent)     │
│                                         │
│  Stage 1: 컬럼명 추출 Loop (최대 3회)    │
│  ┌───────────────┐  ┌────────────────┐  │
│  │  Extractor    │→ │   Reviewer     │  │
│  │  (컬럼 추출)   │  │  (검증/승인)    │  │
│  └───────────────┘  └────────────────┘  │
│                                         │
│  Stage 2: 컬럼명 표준화 Loop             │
│  ┌───────────────┐  ┌────────────────┐  │
│  │ Standardizer  │→ │   Reviewer     │  │
│  │ (DB 스키마 매핑)│  │  (검증/승인)    │  │
│  └───────────────┘  └────────────────┘  │
│                                         │
│  Stage 3: SQL 생성 Loop (최대 3회)       │
│  ┌───────────────┐  ┌────────────────┐  │
│  │ SQL Generator │→ │  SQL Reviewer  │  │
│  │  (SQL 생성)    │  │ (검증 및 실행)  │  │
│  └───────────────┘  └────────────────┘  │
└──────────────┬──────────────────────────┘
               ▼
        CSV 결과 반환
```

---

# 9. 핵심 도구(Tools) 및 유틸리티

## Tools

### 1. 컬럼명 추출 도구 (`column_name_extraction_tools.py`)
```python
def exit_column_extraction_loop(tool_context: ToolContext):
    """컬럼 추출 루프 종료 시그널"""
    # 추출된 컬럼명 상태 확인 후 다음 단계로 에스컬레이션
```

### 2. SQL 생성/실행 도구 (`sql_generator_tools.py`)
```python
async def query_bga_database(generated_sql: str, tool_context: ToolContext):
    """PostgreSQL에서 SQL 실행 → 결과를 CSV로 반환"""
    # psycopg 비동기 커넥션 풀 사용
    # ToolResponseData(csv_table=...) 형태로 반환
```

### 3. 벡터 DB 검색 (`bga_column_name_processor.py`)
```python
def get_sim_search(query_list: list[str], n_results: int = 3):
    """ChromaDB에서 유사 컬럼 설명 검색"""
    # BGE-M3-KO 임베딩 모델 사용
    # 컬럼명 → 임베딩 → 유사도 검색 → 참조 문서 반환
```

## 콜백 체인

| 시점 | 콜백 | 역할 |
|------|-------|------|
| Agent 실행 전 | `save_imgfile_artifact` | 사용자 입력 이미지 저장 |
| Model 호출 전 | `remove_non_text_part` | 인라인 이미지 데이터 제거 (토큰 절약) |
| Model 호출 전 | `get_sql_query_references` | 벡터 DB에서 참조 문서 조회 후 컨텍스트 주입 |
| Tool 실행 후 | `save_file_artifact` | SQL 쿼리 결과를 CSV 아티팩트로 저장 |

---

# 10. 상태 관리 및 데이터 모델

## 상태 키 상수 (`constants.py`)

| 상수 | 값 | 용도 |
|------|-----|------|
| `ARTIFACT_STATES` | `"artifact_states"` | 아티팩트 목록 저장 |
| `BGA_COLUMN_NAMES_STATES` | `"bga_column_names"` | 추출된 컬럼명 저장 |
| `BGA_COLUMN_NAMES_REF_DOCS_STATES` | `"bga_column_names_reference_docs"` | 참조 문서 저장 |
| `NUM_OF_DISPLAYED_DATA` | `5` | 응답에 표시할 최대 행 수 |

## 데이터 모델 (`data_state.py`)

```python
class BaseArtifact(BaseModel):       # 아티팩트 기본 메타데이터
    type: str                        # "table" | "image"
    filename: str
    mime_type: str
    user_query: str

class TabularArtifact(BaseArtifact): # 테이블 데이터 아티팩트
    sql_query: str                   # 실행된 SQL
    data_length: int                 # 총 데이터 행 수

class AppState(BaseModel):           # 전체 앱 상태 컨테이너
    artifacts: list[BaseArtifact]    # 아티팩트 목록 (JSON 직렬화)
```

## 도구 응답 모델 (`tool_response.py`)

```python
class ToolResponse(BaseModel):
    status: str                      # "success" | "error"
    message: str                     # 응답 메시지
    data: ToolResponseData           # 이미지/테이블/CSV/Excel 데이터
```

---

<!-- _class: lead -->
# 감사합니다

### 참고 자료
- [Google ADK 공식 문서](https://google.github.io/adk-docs/)
- [Google Cloud ADK Overview](https://docs.google.com/agent-builder/agent-development-kit/overview)
- [ADK Python GitHub](https://github.com/google/adk-python)
