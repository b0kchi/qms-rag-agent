from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlmodel import Session
from src.app.db.database import get_session
from src.app.graph.builder import build_graph
from src.app.graph.state import AgentState

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

@router.post("/analyze")
async def analyze(
    request_text: str = Form(...), # form-data에서 request_text라는 필드를 필수로 받겠다는 의미 
    user_email: str | None = Form(None), # 값이 없을 시 기본값 None
    file: UploadFile | None = File(None),
    session: Session = Depends(get_session), # session파라미터는 get_session함수가 대신 만들어 주입한다. 
):
    graph = build_graph()

    state: AgentState = {
        "request_text": request_text,
        "user_email": user_email,
        "uploaded_filename": file.filename if file else None,
        "uploaded_mime": file.content_type if file else None,
        "uploaded_bytes": (await file.read()) if file else None,

        "selected_template_ids": [],
        "params": {},
        "phase1_results": [],
        "phase2_results": [],

        "retry_count": 0,
        "max_retry": 2,

        "email_sent": False,
    }

    result = graph.invoke(state, {"session": session}) # 그래프 실행 함수 
    return {
        "run_id": result.get("run_id"),
        "action": result.get("action"),
        "quality_score": result.get("quality_score"),
        "final_answer": result.get("final_answer"),
    }