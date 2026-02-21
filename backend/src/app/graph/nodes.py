from sqlmodel import Session
from src.app.db.models import AnalysisRun

from src.app.services.extractors.pdf_extractor import extract_text_from_pdf_bytes
from src.app.services.extractors.txt_extractor import extract_text_from_txt_bytes
from src.app.services.extractors.hwp_extractor import extract_text_from_hwp_bytes

def create_run(state, config):
    session: Session = config["session"] # 파이썬에서는 '변수명: 타입 = 값' 으로 작성한다.
    run = AnalysisRun(request_text=state["request_text"]) # 테이블에 들어갈 레코드 객체(행 객체)를 메모리에 생성
    session.add(run)
    session.commit() # db에 실제 반영
    session.refresh(run) # db에 저장된 최신 상태를 다시 객체에 반영 
    state["run_id"] = run.id
    return state

def extract_evidence(state, config): # 업로드 파일에서 텍스트 근거 추출
    b = state.get("uploaded_bytes") # 업로드된 파일의 원본 바이트를 가져옴
    mime = (state.get("uploaded_mime") or "").lower()
    name = (state.get("uploaded_filename") or "").lower()

    evidence = None # 추출된 텍스트를 담을 변수
    if b:
        if "pdf" in mime or name.endswith(".pdf"):
            evidence = extract_text_from_pdf_bytes(b)
        elif "text" in mime or name.endswith(".txt"):
            evidence = extract_text_from_txt_bytes(b)
        elif name.endswith(".hwp"):
            evidence = extract_text_from_hwp_bytes(b)

    state["evidence_text"] = (evidence or state["request_text"]).strip() # evidence가 비어있으면 요청 텍스트를 근거로 사용
    return state

def decide_action_agent(state, config): # 에이전트 판단 단계 노드
    # TODO: 여기부터 LLM+tool selection로 바꿀 자리 (Agentic)
    # 지금은 룰 기반 스텁: 텍스트 길이/키워드로 db_lookup 결정
    text = state["evidence_text"] # 근거 텍스트
    if len(text) < 5:
        state["action"] = "reject"
        return state
    state["action"] = "db_lookup"
    return state

def pick_templates_agent(state, config):
    # TODO: LLM이 템플릿 목록을 보고 선택하게 할 자리
    # 지금은 "phase1 2개, phase2 5개"를 가정한 더미 선택
    state["selected_template_ids"] = [1, 2, 3, 4, 5, 6, 7]
    state["params"] = {}  # 추후 (라인/설비/기간 등) 추론
    return state

def run_queries(state, config):
    # TODO: 실제 DB 템플릿 실행기로 교체
    # 지금은 더미 결과
    state["phase1_results"] = [{"template_id": 1, "rows": 10}, {"template_id": 2, "rows": 5}]
    state["phase2_results"] = [{"template_id": i, "rows": 3} for i in range(3, 8)]
    return state

def judge_quality(state, config):
    # Adaptive 게이트(스텁): 결과 row 수로 품질 점수 계산
    total_rows = sum(r.get("rows", 0) for r in state.get("phase1_results", [])) + \
                 sum(r.get("rows", 0) for r in state.get("phase2_results", []))
    score = 0.2 if total_rows == 0 else min(1.0, 0.4 + total_rows / 50.0)
    state["quality_score"] = score

    if score < 0.65:
        state["next_fix"] = "add_queries" if state["retry_count"] < state["max_retry"] else "ask_user"
    else:
        state["next_fix"] = "finalize"
    return state

def adapt_fix(state, config):
    # Adaptive 보강(스텁): 재시도 카운트만 증가
    state["retry_count"] += 1
    return state

def finalize_answer(state, config):
    state["final_answer"] = (
        f"분석 완료(품질점수={state.get('quality_score', 0):.2f}). "
        f"Phase1 {len(state.get('phase1_results', []))}개, "
        f"Phase2 {len(state.get('phase2_results', []))}개 결과를 종합했습니다."
    )
    return state

def persist_run(state, config):
    session: Session = config["session"]
    run = session.get(AnalysisRun, state["run_id"])
    if run:
        run.evidence_text = state.get("evidence_text")
        run.action = state.get("action")
        run.selected_template_ids = ",".join(map(str, state.get("selected_template_ids", [])))
        run.quality_score = state.get("quality_score")
        run.final_answer = state.get("final_answer")
        session.add(run)
        session.commit()
    return state