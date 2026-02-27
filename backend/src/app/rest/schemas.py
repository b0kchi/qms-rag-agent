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

    # vector 옵션
    document_id: str | None = None

    # sql_template 옵션
    template_id: str | None = None
    params: dict[str, Any] | None = None

    # 사용자가 “다시 질문”에 답을 준 경우
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