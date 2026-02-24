from typing import Dict, Any
from sqlmodel import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.repositories.template_repo import TemplateRepo
from app.repositories.sql_repo import SQLRepo
from app.agents.state import AgentState

class SQLAnalysisAgent:
    def __init__(self):
        self.llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)

        self.pick_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You choose the best SQL template for the user query.\n"
             "Return JSON only: {template_name, params}\n"
             "Params must match placeholders in sql_text.\n"
             "If not sure, choose the closest."),
            ("human",
             "User query: {query}\n"
             "Templates:\n{templates}\n")
        ])

        self.summarize_prompt = ChatPromptTemplate.from_messages([
            ("system", "Summarize SQL result for operations. Mention key stats/trends/anomalies if present."),
            ("human", "Query: {query}\nRows: {rows}\n")
        ])

    def run(self, session: Session, state: AgentState) -> AgentState:
        q = state["query"]
        t_repo = TemplateRepo(session)
        s_repo = SQLRepo(session)

        templates = t_repo.list_active()
        templates_view = [
            {"name": t.name, "description": t.description, "sql_params_hint": self._extract_params(t.sql_text)}
            for t in templates
        ]

        # LLM로 템플릿 선택 & 파라미터 추론
        import json
        picked = {"template_name": None, "params": {}}
        try:
            res = self.llm.invoke(self.pick_prompt.format_messages(query=q, templates=templates_view)).content
            picked = json.loads(res)
        except Exception:
            # 최소 fallback
            picked = {"template_name": templates[0].name if templates else None, "params": {}}

        tpl_name = picked.get("template_name")
        params: Dict[str, Any] = picked.get("params", {}) or {}

        tpl = t_repo.get_by_name(tpl_name) if tpl_name else None
        if not tpl:
            state["sql_result"] = {"error": "No SQL template available"}
            return state

        # 실행 (row 제한은 템플릿 자체에서 LIMIT 걸어두는 방식 추천)
        rows = s_repo.run(tpl.sql_text, params)

        summary = ""
        try:
            summary = self.llm.invoke(self.summarize_prompt.format_messages(query=q, rows=rows[:50])).content
        except Exception:
            summary = "SQL summary unavailable."

        state["sql_result"] = {
            "template_name": tpl.name,
            "params": params,
            "rows": rows[:200],  # 안전 제한
            "summary": summary
        }
        return state

    def _extract_params(self, sql_text: str) -> list[str]:
        # :param 형태 추출
        import re
        return list(sorted(set(re.findall(r":([a-zA-Z_][a-zA-Z0-9_]*)", sql_text))))