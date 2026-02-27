# app/agents/orchestrator.py

import json
from sqlmodel import Session

from app.agents.state import AgentState
from app.agents.analyzer import QueryAnalyzer
from app.agents.validation import RetrievalValidator
from app.agents.llm.answerer import LLMAnswerer

from app.agents.strategies.vector import VectorStrategy
from app.agents.strategies.sql_template import SqlTemplateStrategy
from app.agents.strategies.hybrid import HybridStrategy
from app.agents.strategies.graph import GraphStrategy  # graph.py로 분리해뒀다면 사용
# 만약 graph가 hybrid.py 안에 스텁으로 같이 있다면 아래 import로 바꿔줘:
# from app.agents.strategies.hybrid import GraphStrategy

from app.com.utils.text import normalize_query
from app.com.config.settings import settings
from app.com.repositories.sql_template_repo import SqlTemplateRepo
from app.agents.param_extractor import autofill_params, missing_params


class Orchestrator:
    """
    Plan -> Execute(전략 승인/실행) -> Validate(자동 전환/추가질문) -> Answer
    MVP 저장소: 메모리 dict (운영: Redis/DB 권장)
    """

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.validator = RetrievalValidator()
        self.answerer = LLMAnswerer()

        self.strategies = {
            "vector": VectorStrategy(),
            "sql_template": SqlTemplateStrategy(),
            "hybrid": HybridStrategy(),
            "graph": GraphStrategy(),
        }

        self._store: dict[str, AgentState] = {}

    # ----------------------------
    # State
    # ----------------------------
    def create_state(self, conversation_id: str, query: str, session: Session | None = None) -> AgentState:
        state = AgentState(
            conversation_id=conversation_id,
            query_original=query,
            query_normalized=normalize_query(query),
            max_loops=settings.MAX_LOOPS,
        )

        # 전략 후보 제안
        state.proposed_strategies = self.analyzer.propose_strategies(state.query_normalized)

        # SQL 템플릿 후보(선택) - session이 있으면 DB에서 조회해서 매칭
        state.proposed_sql_templates = []
        if session is not None:
            templates = SqlTemplateRepo(session).list_all()
            tpl_dicts = []
            for t in templates:
                try:
                    params = json.loads(t.params_json) if t.params_json else {}
                except Exception:
                    params = {}
                required = list(params.get("required", [])) if isinstance(params, dict) else []
                tpl_dicts.append(
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "required_params": required,
                    }
                )

            matches = self.analyzer.match_sql_templates(state.query_normalized, tpl_dicts)
            matched_ids = {m.template_id for m in matches}
            state.proposed_sql_templates = [t for t in tpl_dicts if t["id"] in matched_ids]

        self._store[conversation_id] = state
        return state

    def get_state(self, conversation_id: str) -> AgentState:
        return self._store[conversation_id]

    # ----------------------------
    # Core execution (with retry)
    # ----------------------------
    def _execute_once(self, session: Session, state: AgentState, strategy_key: str, **kwargs) -> AgentState:
        state.selected_strategy = strategy_key
        strat = self.strategies.get(strategy_key)

        if not strat:
            state.validation_ok = False
            state.validation_issues = [f"Unknown strategy: {strategy_key}"]
            state.pending_user_question = "알 수 없는 전략입니다. 다른 전략을 선택해 주세요."
            return state

        state.loop_count += 1
        state.pending_user_question = None

        retrieval = strat.run(session, state, **kwargs)
        state.retrieval = retrieval

        decision = self.validator.validate(retrieval)
        state.validation_ok = decision.ok
        state.validation_issues = decision.issues

        # 사용자에게 추가 질문이 필요한 케이스
        if decision.ask_user:
            state.pending_user_question = decision.ask_user

        # 자동 재시도/전략 전환
        if (
            (not decision.ok)
            and decision.should_retry
            and decision.retry_with_strategy
            and state.loop_count < state.max_loops
        ):
            return self._execute_once(session, state, decision.retry_with_strategy, **kwargs)

        return state

    # ----------------------------
    # Public API
    # ----------------------------
    def execute(
        self,
        session: Session,
        conversation_id: str,
        selected_strategy: str,
        *,
        document_id: str | None = None,
        template_id: str | None = None,
        params: dict | None = None,
        user_followup: str | None = None,
    ) -> AgentState:
        state = self.get_state(conversation_id)

        # 사용자가 추가 질문에 답을 준 경우: 질의 보강(간단 append)
        if user_followup:
            state.query_original = f"{state.query_original}\n[추가정보] {user_followup}"
            state.query_normalized = normalize_query(state.query_original)

        # --- SQL 템플릿 파라미터 자동 추출/검증 ---
        if selected_strategy == "sql_template":
            if not template_id:
                state.pending_user_question = "어떤 SQL 템플릿으로 조회할까요? template_id를 선택해서 보내주세요."
                state.validation_ok = False
                state.validation_issues = ["template_id missing"]
                return state

            tpl = SqlTemplateRepo(session).get(template_id)
            if not tpl:
                state.pending_user_question = "선택한 SQL 템플릿을 찾을 수 없어요. 다시 선택해줄래요?"
                state.validation_ok = False
                state.validation_issues = ["template not found"]
                return state

            try:
                pj = json.loads(tpl.params_json) if tpl.params_json else {}
            except Exception:
                pj = {}
            required = list(pj.get("required", [])) if isinstance(pj, dict) else []

            filled = autofill_params(required, state.query_original, params or {})
            miss = missing_params(required, filled)

            if miss:
                state.pending_user_question = (
                    f"이 SQL 템플릿 실행에 필요한 값이 부족해요: {', '.join(miss)}. 값을 알려줄래요?"
                )
                state.validation_ok = False
                state.validation_issues = [f"missing params: {miss}"]
                return state

            params = filled  # 채워진 params로 교체

        kwargs = {
            "document_id": document_id,
            "template_id": template_id,
            "params": params or {},
        }

        state = self._execute_once(session, state, selected_strategy, **kwargs)

        # 실패했고 사용자 질문도 없다면: 전략 후보 갱신(프론트에 제안용)
        if not state.validation_ok and not state.pending_user_question:
            state.proposed_strategies = self.analyzer.propose_strategies(state.query_normalized)

        return state

    def answer(self, conversation_id: str) -> tuple[str, list[dict], list[dict]]:
        """
        return: (answer_text, citations, artifacts)
        artifacts: [{"type":"grid"|"echarts","spec":{...}}, ...]
        """
        state = self.get_state(conversation_id)
        if not state.retrieval:
            return "검색 결과가 없어 답변을 생성할 수 없습니다.", [], []

        txt = self.answerer.answer(state.query_original, state.retrieval)

        # ---- artifacts 생성(초기 버전) ----
        artifacts: list[dict] = []
        if state.retrieval.kind == "sql_rows":
            rows = state.retrieval.payload or []
            if rows and isinstance(rows[0], list):
                cols = [f"col_{i}" for i in range(len(rows[0]))]
                artifacts.append(
                    {
                        "type": "grid",
                        "spec": {
                            "columns": [{"field": c, "headerName": c} for c in cols],
                            "rows": [dict(zip(cols, r)) for r in rows[:200]],
                        },
                    }
                )

                # 2열 이상이면 간단 bar chart 샘플
                if len(cols) >= 2:
                    def _to_float(x):
                        try:
                            return float(x)
                        except Exception:
                            return 0.0

                    artifacts.append(
                        {
                            "type": "echarts",
                            "spec": {
                                "title": {"text": "SQL 결과 시각화(샘플)"},
                                "tooltip": {},
                                "xAxis": {"type": "category", "data": [str(r[0]) for r in rows[:50]]},
                                "yAxis": {"type": "value"},
                                "series": [{"type": "bar", "data": [_to_float(r[1]) for r in rows[:50]]}],
                            },
                        }
                    )

        return txt, (state.retrieval.citations if state.retrieval else []), artifacts