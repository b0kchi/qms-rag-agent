from dataclasses import dataclass, field
from typing import Any

@dataclass
class ProposedStrategy:
    key: str
    title: str
    rationale: str

@dataclass
class RetrievalResult:
    kind: str  # "chunks" | "sql_rows" | "graph"
    payload: Any
    citations: list[dict] = field(default_factory=list)

@dataclass
class AgentState:
    conversation_id: str
    query_original: str
    query_normalized: str

    proposed_strategies: list[ProposedStrategy] = field(default_factory=list)
    selected_strategy: str | None = None

    # SQL template 후보(Plan에서 보여주기 위함)
    proposed_sql_templates: list[dict] = field(default_factory=list)  # [{id,name,description,required_params}]

    # 실행 결과
    retrieval: RetrievalResult | None = None
    validation_ok: bool = False
    validation_issues: list[str] = field(default_factory=list)

    # 루프/추가질문
    loop_count: int = 0
    max_loops: int = 3
    pending_user_question: str | None = None  # 사용자에게 추가로 물어볼 질문