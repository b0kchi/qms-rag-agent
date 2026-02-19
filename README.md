# QMS RAG Agent (LangGraph + FastAPI + PostgreSQL/pgvector)

제조/QMS 환경에서 사용자의 요구사항을 입력으로 받아,
1) 서비스 적합성 검증 → 2) 1차 원인 분석(저장된 쿼리 2개 실행) →  
3) 2차 원인 분석(저장된 쿼리 5개 실행) → 4) 관련성/근거 검증 → 5) 최종 응답
까지를 **LangGraph 워크플로우(분기/재시도/검증)** 로 구현하는 프로젝트입니다.

> 목표: “LLM을 그냥 호출”이 아니라, **정해진 분석 절차 + 데이터 근거(SQL 결과)** 기반으로
> 재현 가능한 원인분석 에이전트를 만든다.

---

## Key Features

- **요구사항 적합성 검증**
  - 입력이 우리 서비스 범위인지, 제공 가능한 분석인지 판단
  - 부적합 시 거절/추가질문 등 분기 처리

- **1차 원인 분석 (Phase 1)**
  - 사전에 등록된 SQL 템플릿 **2개** 실행
  - 결과를 요약/정리하여 2차 분석 입력으로 사용

- **2차 원인 분석 (Phase 2)**
  - 사전에 등록된 SQL 템플릿 **5개** 실행
  - Phase 1 결과를 바탕으로 심화 분석

- **관련성/근거 검증**
  - “요구사항 ↔ (쿼리 결과/분석) 관련성”
  - “최종 답변 ↔ 근거(쿼리 결과) 일치 여부”
  - 점수/룰 기반 체크 후 분기(재시도/보완/에스컬레이션)

- **DB 연계**
  - PostgreSQL에 “저장된 SQL 템플릿” 관리
  - 실행 로그/결과 요약 저장(옵션)

---

## Architecture (High-level)

User Request
  → [validate_request]
    → (reject / ask_more / proceed)
  → [run_phase1_queries]  (2 queries)
  → [phase1_relevance_check]
    → (ask_more / proceed)
  → [run_phase2_queries]  (5 queries)
  → [phase2_relevance_check]
    → (retry / escalate / finalize)
  → Final Answer

---

## Tech Stack

- Python 3.11+ (권장)
- FastAPI
- LangGraph / LangChain
- PostgreSQL + pgvector
- SQLAlchemy / SQLModel

---

## Project Structure
qms-rag-agent/
&nbsp;&nbsp;backend/
&nbsp;&nbsp;&nbsp;&nbsp;src/app/
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;main.py # FastAPI entrypoint
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;graph/ # LangGraph workflow (state/nodes/builder)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;services/ # SQL runner, relevance checker
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;models.py # DB models (SQL templates, logs)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;api/routes.py # HTTP endpoints

---

## Getting Started

### 1) Start PostgreSQL + pgvector (Docker)
프로젝트 루트에서:
```bash
docker compose up -d
```

기본 DB 접속 정보:
- host: localhost
- port: 5432
- user: postgres
- password: postgres
- db: qmsrag


### 2) Backend Setup (Windows)
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
```

패키지 설치(예: requirements.txt 방식인 경우):
```bash
pip install -r requirements.txt

```

### 3) Env 설정
backend/.env.example을 복사해서 backend/.env 생성:
```bash
copy .env.example .env
```

### 4) Run API
```bash
uvicorn src.app.main:app --reload --port 8000
```

---

### API (Draft)
- POST /analyze
    - 입력: 요구사항 텍스트 + (옵션) 추가 파라미터(기간/설비/라인 등)
    - 처리: LangGraph 워크플로우 실행
    - 출력: 단계별 결과(검증/1차/2차/검증/최종응답)

---

### Data Model (Draft) 
- sql_templates
    - id, name, phase (1 or 2), sql_text, description, is_active
- analysis_runs (옵션)
    - id, request_text, phase1_summary, phase2_summary, final_answer, created_at

---

### Roadmap
- Phase1/Phase2 SQL 템플릿 테이블 스키마 확정 + seed 데이터
- LangGraph 노드 구현(분기/재시도/관련성 체크)
- 실행 로그/감사로그(운영용)
- Spring 연동(옵션): Spring → FastAPI 내부 호출 구조로 확장
- Frontend(옵션): React로 분석 요청/결과 타임라인 UI

---

### Notes
폐쇄망 환경에서는 LLM/Embedding을 로컬 모델(Ollama/LM Studio 등)로 교체 가능하도록 설계합니다.
SQL은 “사전 승인된 템플릿”만 실행하도록 하여 안전성을 확보합니다.