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

