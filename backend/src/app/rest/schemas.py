from datetime import datetime
from pydantic import BaseModel
from typing import Any, Literal


class PlanRequest(BaseModel):
    query: str


class StrategyOption(BaseModel):
    key: str
    title: str
    rationale: str


class SqlTemplateOption(BaseModel):
    template_id: str
    name: str
    description: str
    required_params: list[str]


class PlanResponse(BaseModel):
    conversation_id: str
    strategies: list[StrategyOption]
    sql_templates: list[SqlTemplateOption] = []
    question_to_user: str


class ExecuteRequest(BaseModel):
    conversation_id: str
    selected_strategy: str

    # vector option
    document_id: str | None = None

    # sql_template option
    template_id: str | None = None
    params: dict[str, Any] | None = None

    # user follow-up answer
    user_followup: str | None = None


class NextAction(BaseModel):
    type: Literal["ASK_USER", "SUGGEST_STRATEGY", "READY_TO_ANSWER"]
    message: str
    suggestions: list[StrategyOption] = []


class ExecuteResponse(BaseModel):
    conversation_id: str
    selected_strategy: str

    validation_ok: bool
    validation_issues: list[str]

    retrieval_kind: str | None = None
    preview: Any | None = None
    citations: list[dict] = []

    next_action: NextAction


class Artifact(BaseModel):
    type: Literal["echarts", "grid"]
    spec: dict[str, Any]


class AnswerRequest(BaseModel):
    conversation_id: str


class AnswerResponse(BaseModel):
    conversation_id: str
    answer_text: str
    citations: list[dict] = []
    artifacts: list[Artifact] = []


class ChatMessage(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatSessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: str | None = None


class SessionCreateRequest(BaseModel):
    title: str | None = None


class SessionCreateResponse(BaseModel):
    session: ChatSessionSummary


class SessionListResponse(BaseModel):
    sessions: list[ChatSessionSummary]


class SessionMessagesResponse(BaseModel):
    session: ChatSessionSummary
    messages: list[ChatMessage]


class SessionMessageRequest(BaseModel):
    message: str


class SessionMessageResponse(BaseModel):
    session: ChatSessionSummary
    user_message: ChatMessage
    assistant_message: ChatMessage
