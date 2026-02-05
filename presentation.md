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
2. 핵심 개념 — Agent 유형 총정리
3. 핵심 개념 — Tool (도구) 심화
4. 핵심 개념 — Callback & Session/Memory
5. 핵심 개념 — Agent 정의 코드 예시
6. Multi-Agent 시스템 아키텍처
7. Multi-Agent — 에이전트 간 통신 패턴
8. Multi-Agent — 워크플로우 오케스트레이션 패턴
9. 주요 기능 및 개발자 도구
10. 배포 및 에코시스템

### Part 2. Data Search Agent 프로젝트
11. 프로젝트 개요 및 목적
12. 디렉토리 구조
13. Agent 구성 및 실행 흐름
14. 핵심 도구(Tools) 및 유틸리티
15. 상태 관리 및 데이터 모델

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

# 2. 핵심 개념 — Agent 유형 총정리

## Agent란?

에이전트는 ADK에서 **특정 작업을 수행하는 자율적 단위**. 두 가지 대분류로 나뉩니다.

### LLM 기반 에이전트 (지능형)

| 클래스 | 특징 | 사용 시점 |
|--------|------|----------|
| `LlmAgent` (`Agent`) | LLM을 사용하여 **추론·의사결정·도구 호출** 수행 | 자연어 이해, 분류, 판단이 필요한 작업 |

- `instruction`: 에이전트의 역할과 행동 규칙 정의 (프롬프트)
- `model`: 사용할 LLM 모델 지정 (Gemini, LiteLLM 등)
- `tools`: 에이전트가 호출 가능한 도구 목록
- `sub_agents`: 작업을 위임할 하위 에이전트 목록
- `output_key`: 에이전트 응답을 세션 상태에 자동 저장

### 워크플로우 에이전트 (비LLM, 결정론적)

| 클래스 | 실행 방식 | 사용 시점 |
|--------|----------|----------|
| `SequentialAgent` | 하위 에이전트를 **순서대로** 실행 | 파이프라인, 단계별 처리 |
| `LoopAgent` | 종료 조건까지 **반복** 실행 | 검증-수정 사이클, 반복 정제 |
| `ParallelAgent` | 하위 에이전트를 **병렬** 실행 | 독립적 작업 동시 처리 |

> 워크플로우 에이전트는 LLM 호출 없이 **제어 흐름만 담당**하므로 비용 없이 오케스트레이션 가능

---

# 3. 핵심 개념 — Tool (도구) 심화

## Tool이란?

에이전트에게 **대화 이외의 능력**을 부여하는 실행 가능한 함수

> LLM은 "무엇을 할지" 결정하고, Tool은 "실제로 실행"합니다

## Tool 유형 분류

| 유형 | 설명 | 예시 |
|------|------|------|
| **Function Tool** | Python 함수를 도구로 등록 | `def search_db(query): ...` |
| **Agent Tool** | 다른 에이전트를 도구로 호출 | `AgentTool(agent=sub_agent)` |
| **Built-in Tool** | ADK 기본 제공 도구 | Google Search, Code Execution |
| **MCP Tool** | Model Context Protocol 서버 연동 | 외부 MCP 서버의 도구 |
| **Third-party Tool** | LangChain 등 외부 프레임워크 도구 | LangChain Tool 래핑 |

## Function Tool 정의 패턴

```python
# 방법 1: 함수 정의 → ADK가 자동으로 스키마 생성
def get_weather(city: str) -> dict:
    """도시의 현재 날씨를 조회합니다."""  # ← docstring이 LLM에 설명으로 전달
    return {"city": city, "temp": 22}

# 방법 2: ToolContext로 에이전트 상태 접근
def save_result(data: str, tool_context: ToolContext):
    """결과를 세션 상태에 저장합니다."""
    tool_context.state["result"] = data
```

> `ToolContext`를 매개변수에 포함하면 ADK가 자동 주입 → **세션 상태, 아티팩트에 접근 가능**

---

# 4. 핵심 개념 — Callback & Session/Memory

## Callback (콜백) 시스템

에이전트 실행 **라이프사이클의 특정 시점**에 커스텀 로직을 삽입하는 메커니즘

```
요청 수신
  │
  ▼
┌─ before_agent_callback ──────────────────────────┐
│                                                   │
│  ┌─ before_model_callback ────────────────────┐  │
│  │  LLM 호출                                   │  │
│  └─ after_model_callback ─────────────────────┘  │
│                                                   │
│  ┌─ before_tool_callback ─────────────────────┐  │
│  │  Tool 실행                                   │  │
│  └─ after_tool_callback ──────────────────────┘  │
│                                                   │
└─ after_agent_callback ───────────────────────────┘
  │
  ▼
응답 반환
```

| 콜백 | 주요 활용 사례 |
|------|---------------|
| `before_agent_callback` | 입력 전처리, 인증 검사, 아티팩트 저장 |
| `after_agent_callback` | 결과 후처리, 로깅, 상태 정리 |
| `before_model_callback` | 프롬프트 수정, 컨텍스트 주입, 토큰 최적화 |
| `after_model_callback` | 응답 필터링, 안전성 검사 |
| `before_tool_callback` | 파라미터 검증, 권한 확인 |
| `after_tool_callback` | 결과 변환, 아티팩트 저장 |

## Session & Memory

| 구분 | 저장소 | 수명 | 용도 |
|------|--------|------|------|
| **Session State** | `session.state` | 대화 세션 동안 | 현재 대화의 임시 데이터 |
| **Memory Service** | Memory Store | 세션 간 영구 | 사용자 선호도, 과거 대화 요약 |

---

# 5. 핵심 개념 — Agent 정의 코드 예시

## LLM Agent 정의

```python
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

root_agent = Agent(
    name="root_agent",
    model=LiteLlm(model="gemini/gemini-2.0-flash"),  # 모델 지정
    instruction="당신은 데이터 분석 도우미입니다...",   # 시스템 프롬프트
    tools=[search_db, generate_chart],                # 사용 가능한 도구
    sub_agents=[data_agent, report_agent],            # 하위 에이전트
    before_agent_callback=my_pre_hook,                # 콜백 등록
    output_key="agent_response",                      # 상태 자동 저장
)
```

## 워크플로우 에이전트 조합 예시

```python
from google.adk.agents import SequentialAgent, LoopAgent

# 추출 → 검증 반복 루프
extraction_loop = LoopAgent(
    name="extraction_loop",
    max_iterations=3,                     # 최대 반복 횟수
    sub_agents=[extractor, reviewer],     # 순서대로 반복 실행
)

# 전체 파이프라인: 추출 루프 → SQL 생성 루프
pipeline = SequentialAgent(
    name="pipeline",
    sub_agents=[extraction_loop, sql_loop],  # 순차 실행
)
```

## 핵심 포인트

| 개념 | 설명 |
|------|------|
| **Agent = 선언적 정의** | 클래스 인스턴스 생성으로 에이전트 구성 완료 |
| **조합 가능 (Composable)** | 에이전트 안에 에이전트를 중첩하여 복잡한 워크플로우 구성 |
| **관심사 분리** | 각 에이전트는 하나의 역할만 담당 → 테스트·디버깅 용이 |
| **프롬프트 외부화** | YAML 파일에서 프롬프트를 로드하여 코드와 분리 가능 |

---

# 6. Multi-Agent 시스템 아키텍처

## 이벤트 기반 런타임 (Event-Driven Runtime)

ADK 런타임은 에이전트·도구·콜백 간의 모든 상호작용을 **Event 스트림**으로 처리합니다.

```
┌──────────────────────────────────────────────────────────┐
│                      ADK Runtime                         │
│                                                          │
│  User ──▶ Runner ──▶ Session ──▶ Agent ──▶ Event Stream  │
│                         │                       │        │
│                    ┌────┴────┐            ┌─────┴─────┐  │
│                    │  State  │            │   Events   │  │
│                    │ (dict)  │            │ (stream)   │  │
│                    └─────────┘            └───────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 핵심 런타임 컴포넌트

| 컴포넌트 | 역할 |
|----------|------|
| **Runner** | 에이전트 실행을 시작하고 이벤트를 수집하는 진입점 |
| **Session** | 대화 컨텍스트, 상태(state), 이벤트 히스토리 관리 |
| **Event** | 에이전트·도구 실행 결과를 담는 불변 데이터 단위 |
| **State** | 에이전트 간 데이터를 공유하는 딕셔너리 (`session.state`) |
| **Artifact Service** | 파일(CSV, 이미지 등)을 저장·조회하는 서비스 |

## 에이전트 계층 구조

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

---

# 7. Multi-Agent — 에이전트 간 통신 패턴

## 3가지 통신 메커니즘

### 1. LLM 기반 전달 (Transfer / Delegation)

LLM이 **자율적으로 판단**하여 하위 에이전트에게 작업을 위임

```
Root Agent (LLM 판단)
  │ "이 질문은 데이터 검색이 필요하다"
  ▼
Data Search Agent ──▶ 결과를 Root Agent에 반환
```

- `sub_agents=[agent_a, agent_b]`로 등록하면 LLM이 적절한 에이전트 선택
- 유연하지만 LLM 판단에 의존 → 비결정론적

### 2. AgentTool (명시적 도구 호출)

에이전트를 **Tool처럼** 명시적으로 호출 → 결과를 즉시 받아 활용

```python
from google.adk.tools import AgentTool

research_tool = AgentTool(agent=research_agent)

main_agent = Agent(
    tools=[research_tool],  # 에이전트를 도구로 등록
)
```

- 호출하는 에이전트가 **제어권을 유지**
- 결과를 받아 후속 처리 가능 → 파이프라인에 적합

### 3. A2A 프로토콜 (Agent-to-Agent)

**원격 에이전트** 간 표준화된 통신 프로토콜

- 서로 다른 프레임워크, 서로 다른 서버에서 실행되는 에이전트 연결
- JSON-RPC 기반 메시지 교환
- 에이전트 디스커버리, 태스크 관리, 스트리밍 지원

---

# 8. Multi-Agent — 워크플로우 오케스트레이션 패턴

## 대표적 오케스트레이션 패턴 비교

### 패턴 1: Sequential (순차 파이프라인)

```
┌────────┐    ┌────────┐    ┌────────┐
│ Step 1 │ ──▶│ Step 2 │ ──▶│ Step 3 │
│ 데이터  │    │  변환   │    │  출력   │
│  수집   │    │  처리   │    │  생성   │
└────────┘    └────────┘    └────────┘
```

**적용**: ETL 파이프라인, 단계별 데이터 정제, 문서 처리

### 패턴 2: Loop + Review (반복 검증)

```
     ┌──────────────────────────────┐
     │                              │
     ▼                              │
┌──────────┐    ┌──────────┐   NG   │
│ Generator│ ──▶│ Reviewer │ ──────┘
│ (생성)    │    │ (검증)    │
└──────────┘    └────┬─────┘
                     │ OK
                     ▼
                  다음 단계
```

**적용**: SQL 생성-검증, 코드 리뷰, 품질 검사 루프

### 패턴 3: Parallel + Aggregation (병렬 수집)

```
              ┌──────────┐
         ┌───▶│ Source A │───┐
         │    └──────────┘   │
┌────────┤    ┌──────────┐   ├───▶ ┌────────────┐
│ Splitter├───▶│ Source B │───┤     │ Aggregator │
└────────┤    └──────────┘   │     └────────────┘
         │    ┌──────────┐   │
         └───▶│ Source C │───┘
              └──────────┘
```

**적용**: 다중 소스 검색, A/B 비교 분석, 앙상블 생성

### 패턴 4: Hierarchical (계층적 위임) — 본 프로젝트에서 사용

```
┌────────────────────────────────────────────┐
│  Root Agent (최상위 오케스트레이터)           │
│  └─ SequentialAgent (파이프라인)             │
│       ├─ LoopAgent (컬럼 추출 반복 검증)     │
│       │    ├─ LlmAgent (Extractor)          │
│       │    └─ LlmAgent (Reviewer)           │
│       └─ LoopAgent (SQL 생성 반복 검증)      │
│            ├─ LlmAgent (Generator)          │
│            └─ LlmAgent (Reviewer)           │
└────────────────────────────────────────────┘
```

> 여러 패턴을 **중첩·조합**하여 복잡한 워크플로우를 선언적으로 구성 가능

---

# 9. 주요 기능 및 개발자 도구

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

# 10. 배포 및 에코시스템

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

# 11. 프로젝트 개요 및 목적

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

# 12. 디렉토리 구조

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

# 13. Agent 구성 및 실행 흐름

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

# 14. 핵심 도구(Tools) 및 유틸리티

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

# 15. 상태 관리 및 데이터 모델

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
