from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.rest.schemas import (
    PlanRequest, PlanResponse, StrategyOption, SqlTemplateOption,
    ExecuteRequest, ExecuteResponse, NextAction,
    AnswerRequest, AnswerResponse, Artifact,
)
from app.com.utils.ids import new_id
from app.com.db.session import get_session
from app.agents.orchestrator import Orchestrator

router = APIRouter()
orch = Orchestrator()


@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest, session: Session = Depends(get_session)):
    cid = new_id("conv")
    state = orch.create_state(cid, req.query, session=session)

    strategies = [StrategyOption(key=s.key, title=s.title, rationale=s.rationale) for s in state.proposed_strategies]
    templates = [
        SqlTemplateOption(
            template_id=t["id"],
            name=t["name"],
            description=t["description"],
            required_params=t.get("required_params", []),
        )
        for t in state.proposed_sql_templates
    ]

    q = "어떤 검색 방식으로 진행할까요? (전략을 선택해 주세요)"
    if templates:
        q += " / 또는 SQL 템플릿을 선택해 조회할 수도 있어요."

    return PlanResponse(
        conversation_id=cid,
        strategies=strategies,
        sql_templates=templates,
        question_to_user=q,
    )


@router.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest, session: Session = Depends(get_session)):
    state = orch.execute(
        session,
        conversation_id=req.conversation_id,
        selected_strategy=req.selected_strategy,
        document_id=req.document_id,
        template_id=req.template_id,
        params=req.params,
        user_followup=req.user_followup,
    )

    preview = None
    citations = []
    kind = None
    if state.retrieval:
        kind = state.retrieval.kind
        citations = state.retrieval.citations
        payload = state.retrieval.payload
        if isinstance(payload, list):
            preview = payload[:3]
        else:
            preview = payload

    # next_action 결정
    if state.validation_ok:
        next_action = NextAction(type="READY_TO_ANSWER", message="근거가 충분합니다. 답변을 생성할까요?", suggestions=[])
    elif state.pending_user_question:
        next_action = NextAction(type="ASK_USER", message=state.pending_user_question, suggestions=[])
    else:
        suggestions = [StrategyOption(key=s.key, title=s.title, rationale=s.rationale) for s in state.proposed_strategies]
        next_action = NextAction(
            type="SUGGEST_STRATEGY",
            message="현재 근거가 부족합니다. 다른 전략으로 시도해볼까요?",
            suggestions=suggestions,
        )

    return ExecuteResponse(
        conversation_id=state.conversation_id,
        selected_strategy=state.selected_strategy or "",
        validation_ok=state.validation_ok,
        validation_issues=state.validation_issues,
        retrieval_kind=kind,
        preview=preview,
        citations=citations,
        next_action=next_action,
    )


@router.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest):
    txt, citations, artifacts = orch.answer(req.conversation_id)
    return AnswerResponse(
        conversation_id=req.conversation_id,
        answer_text=txt,
        citations=citations,
        artifacts=[Artifact(**a) for a in artifacts],
    )