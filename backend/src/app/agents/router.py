import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.agents.state import AgentState

def rule_hints(query: str) -> Dict[str, Any]:
    has_numbers = bool(re.search(r"\d", query))
    has_time = bool(re.search(r"(오늘|어제|최근|지난|일|주|월|분기|\d+\s*일|\d+\s*주)", query))
    has_agg = any(k in query for k in ["몇 건", "추세", "비율", "Top", "TOP", "상위", "집계", "평균", "분산", "이상치"])
    has_doc = any(k in query for k in ["절차", "가이드", "정의", "기준", "요구사항", "규정", "CAPA", "SOP"])
    has_relation = any(k in query for k in ["원인", "결과", "연관", "영향", "연쇄", "상관", "왜", "때문"])

    has_lot = bool(re.search(r"\bLOT\b|LOT[_-]?[A-Z0-9]+", query, re.IGNORECASE))
    has_equip = bool(re.search(r"\b(EQP|EQUIP)\b|EQUIP[_-]?[A-Z0-9]+", query, re.IGNORECASE))
    has_defect = ("불량" in query) or bool(re.search(r"DEFECT[_-]?[A-Z0-9]+", query, re.IGNORECASE))

    return {
        "has_numbers": has_numbers,
        "has_time": has_time,
        "has_agg": has_agg,
        "has_doc": has_doc,
        "has_relation": has_relation,
        "has_lot": has_lot,
        "has_equip": has_equip,
        "has_defect": has_defect,
    }

class RouterSupervisor:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )

        # ⚠️ 주의: 템플릿 변수는 {query}와 {hints}만 사용 (쉼표 포함 변수 금지)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a routing supervisor for a QMS RAG system.\n"
             "Choose strategy among VECTOR, GRAPH, SQL, HYBRID.\n"
             "Return JSON only: {\"strategy\":\"...\",\"plan\":[...],\"rationale\":\"...\"}.\n"
             "Plan steps must be subset/order of: SQL, VECTOR, GRAPH, JUDGE.\n"
             "Use rules: SQL when query needs exact counts/period/filters; VECTOR for document definitions/requirements; "
             "GRAPH for cause-effect or entity relationship tracing; HYBRID when mixed."),
            ("human",
             "User query: {query}\n"
             "Hints: {hints}\n")
        ])

    def route(self, state: AgentState) -> AgentState:
        q = state["query"]
        hints = rule_hints(q)

        # 1) 룰 기반 기본값
        if hints["has_doc"] and (hints["has_numbers"] or hints["has_relation"]):
            default_strategy, default_plan = "HYBRID", ["SQL", "VECTOR", "GRAPH", "JUDGE"]
        elif hints["has_doc"]:
            default_strategy, default_plan = "VECTOR", ["VECTOR", "JUDGE"]
        elif hints["has_relation"]:
            default_strategy, default_plan = "GRAPH", ["GRAPH", "JUDGE"]
        elif hints["has_numbers"] or hints["has_agg"] or hints["has_time"] or hints["has_lot"] or hints["has_equip"] or hints["has_defect"]:
            default_strategy, default_plan = "SQL", ["SQL", "JUDGE"]
        else:
            default_strategy, default_plan = "VECTOR", ["VECTOR", "JUDGE"]

        # 2) LLM로 보정
        strategy, plan, rationale = default_strategy, default_plan, "rule-based routing"
        try:
            import json
            msg = self.prompt.format_messages(query=q, hints=hints)
            res = self.llm.invoke(msg).content
            obj = json.loads(res)

            strategy = obj.get("strategy", strategy)
            plan = obj.get("plan", plan)
            rationale = obj.get("rationale", rationale)
        except Exception:
            # LLM이 실패해도 기본값 유지
            pass

        state["hints"] = hints
        state["strategy"] = strategy
        state["plan"] = plan
        state["rationale"] = rationale
        return state