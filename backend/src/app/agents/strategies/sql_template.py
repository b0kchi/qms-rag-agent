from sqlmodel import Session, text
from app.agents.strategies.base import Strategy
from app.agents.state import AgentState, RetrievalResult
from app.com.repositories.sql_template_repo import SqlTemplateRepo


class SqlTemplateStrategy(Strategy):
    key = "sql_template"

    def run(self, session: Session, state: AgentState, **kwargs) -> RetrievalResult:
        template_id: str = kwargs.get("template_id")
        params: dict = kwargs.get("params") or {}

        if not template_id:
            return RetrievalResult(
                kind="sql_rows",
                payload=[],
                citations=[],
            )

        repo = SqlTemplateRepo(session)
        tpl = repo.get(template_id)
        if not tpl:
            return RetrievalResult(kind="sql_rows", payload=[], citations=[])

        rows = session.exec(text(tpl.sql_text), params).all()
        # rows가 Row 객체일 수 있어 dict 변환은 운영에서 정리(스켈레톤은 그대로)
        return RetrievalResult(
            kind="sql_rows",
            payload=[list(r) for r in rows],
            citations=[{"sql_template_id": tpl.id, "sql_template_name": tpl.name}],
        )