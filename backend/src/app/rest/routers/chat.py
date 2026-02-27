from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.rest.schemas import (
    PlanRequest,
    PlanResponse,
    StrategyOption,
    SqlTemplateOption,
    ExecuteRequest,
    ExecuteResponse,
    NextAction,
    AnswerRequest,
    AnswerResponse,
    Artifact,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionListResponse,
    SessionMessagesResponse,
    SessionMessageRequest,
    SessionMessageResponse,
    ChatMessage,
    ChatSessionSummary,
)
from app.com.utils.ids import new_id
from app.com.db.session import get_session
from app.agents.orchestrator import Orchestrator
from app.schema.models.chat_message import ChatMessageModel
from app.schema.models.chat_session import ChatSessionModel

router = APIRouter()
orch = Orchestrator()


def _now() -> datetime:
    return datetime.utcnow()


def _assistant_reply(user_turns: int, user_text: str) -> str:
    return (
        f"세션 문맥 {user_turns}건을 참고해 답변합니다.\n"
        f"현재는 UI/세션 관리 단계이며, 질문을 정상 수신했습니다: {user_text}"
    )


def _build_context_query(session: Session, session_id: str, latest_text: str, window: int = 5) -> str:
    stmt = (
        select(ChatMessageModel)
        .where(
            ChatMessageModel.session_id == session_id,
            ChatMessageModel.role == "user",
        )
        .order_by(ChatMessageModel.created_at.desc())
        .limit(window)
    )
    rows = session.exec(stmt).all()
    past = [r.content for r in reversed(rows)]
    return "\n".join([*past, latest_text]).strip()


def _generate_orchestrated_reply(session: Session, session_id: str, user_text: str, user_turns: int) -> str:
    try:
        query = _build_context_query(session, session_id, user_text)
        state = orch.create_state(session_id, query, session=session)
        state = orch.execute(session, conversation_id=session_id, selected_strategy="vector")
        if state.validation_ok:
            answer, _, _ = orch.answer(session_id)
            return answer
        if state.pending_user_question:
            return state.pending_user_question
        if state.validation_issues:
            return "근거가 부족합니다. " + " / ".join(state.validation_issues)
    except Exception:
        # 비정상 상황에서는 기본 응답으로 폴백
        pass
    return _assistant_reply(user_turns, user_text)


def _session_summary(row: ChatSessionModel, last_preview: str | None) -> ChatSessionSummary:
    return ChatSessionSummary(
        session_id=row.id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_message_preview=last_preview,
    )


def _last_preview(session: Session, session_id: str) -> str | None:
    stmt = (
        select(ChatMessageModel)
        .where(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at.desc())
        .limit(1)
    )
    last = session.exec(stmt).first()
    return last.content[:120] if last else None


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(session: Session = Depends(get_session)):
    rows = session.exec(select(ChatSessionModel).order_by(ChatSessionModel.updated_at.desc())).all()
    summaries = [_session_summary(row, _last_preview(session, row.id)) for row in rows]
    return SessionListResponse(sessions=summaries)


@router.post("/sessions", response_model=SessionCreateResponse)
def create_session(req: SessionCreateRequest, session: Session = Depends(get_session)):
    count_stmt = select(ChatSessionModel.id)
    current_count = len(session.exec(count_stmt).all())
    title = req.title.strip() if req.title and req.title.strip() else f"새 대화 {current_count + 1}"

    row = ChatSessionModel(
        id=new_id("sess"),
        title=title,
        created_at=_now(),
        updated_at=_now(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    return SessionCreateResponse(session=_session_summary(row, None))


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
def get_session_messages(session_id: str, session: Session = Depends(get_session)):
    row = session.get(ChatSessionModel, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_stmt = (
        select(ChatMessageModel)
        .where(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.created_at.asc())
    )
    message_rows = session.exec(messages_stmt).all()

    messages = [
        ChatMessage(
            message_id=m.id,
            role=m.role,  # type: ignore[arg-type]
            content=m.content,
            created_at=m.created_at,
        )
        for m in message_rows
    ]

    return SessionMessagesResponse(session=_session_summary(row, _last_preview(session, row.id)), messages=messages)


@router.post("/sessions/{session_id}/messages", response_model=SessionMessageResponse)
def send_session_message(session_id: str, req: SessionMessageRequest, session: Session = Depends(get_session)):
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message is empty")

    row = session.get(ChatSessionModel, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    user_turns_stmt = select(ChatMessageModel.id).where(
        ChatMessageModel.session_id == session_id,
        ChatMessageModel.role == "user",
    )
    user_turns = len(session.exec(user_turns_stmt).all()) + 1

    user_msg = ChatMessageModel(
        id=new_id("msg"),
        session_id=session_id,
        role="user",
        content=text,
        created_at=_now(),
    )
    session.add(user_msg)
    session.flush()

    reply_text = _generate_orchestrated_reply(session, session_id, text, user_turns)

    assistant_msg = ChatMessageModel(
        id=new_id("msg"),
        session_id=session_id,
        role="assistant",
        content=reply_text,
        created_at=_now(),
    )

    row.updated_at = _now()
    session.add(assistant_msg)
    session.add(row)
    session.commit()
    session.refresh(row)

    summary = _session_summary(row, assistant_msg.content[:120])

    return SessionMessageResponse(
        session=summary,
        user_message=ChatMessage(
            message_id=user_msg.id,
            role="user",
            content=user_msg.content,
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessage(
            message_id=assistant_msg.id,
            role="assistant",
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
        ),
    )


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

    question = "어떤 검색 방식을 선택하시겠습니까?"
    if templates:
        question += " 또는 SQL 템플릿을 선택해 조회할 수 있습니다."

    return PlanResponse(
        conversation_id=cid,
        strategies=strategies,
        sql_templates=templates,
        question_to_user=question,
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
        preview = payload[:3] if isinstance(payload, list) else payload

    if state.validation_ok:
        next_action = NextAction(type="READY_TO_ANSWER", message="근거가 충분합니다. 답변을 생성할까요?", suggestions=[])
    elif state.pending_user_question:
        next_action = NextAction(type="ASK_USER", message=state.pending_user_question, suggestions=[])
    else:
        suggestions = [StrategyOption(key=s.key, title=s.title, rationale=s.rationale) for s in state.proposed_strategies]
        next_action = NextAction(
            type="SUGGEST_STRATEGY",
            message="현재 근거가 부족합니다. 다른 전략으로 재시도할까요?",
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
