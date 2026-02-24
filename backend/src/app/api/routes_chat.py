from fastapi import APIRouter
from pydantic import BaseModel

from app.db.engine import engine
from sqlmodel import Session

from app.agents.graph_workflow import make_workflow

router = APIRouter(prefix="/chat", tags=["chat"])

def get_session():
    return Session(engine)

workflow = make_workflow(get_session)

class ChatRequest(BaseModel):
    query: str

@router.post("")
def chat(req: ChatRequest):
    init_state = {
        "query": req.query,
        "vector_hits": [],
        "graph_result": {},
        "sql_result": {},
        "loop_count": 0,
    }
    out = workflow.invoke(init_state)
    return {
        "strategy": out.get("strategy"),
        "plan": out.get("plan"),
        "rationale": out.get("rationale"),
        "final_answer": out.get("final_answer"),
        "need_more": out.get("need_more"),
        "improve_request": out.get("improve_request"),
        "debug": {
            "vector_hits": out.get("vector_hits", [])[:5],
            "graph_entities": (out.get("graph_result") or {}).get("entities", []),
            "sql_template": (out.get("sql_result") or {}).get("template_name"),
        }
    }