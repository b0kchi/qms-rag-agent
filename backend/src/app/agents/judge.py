import json
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.agents.state import AgentState


class SynthesizerJudge:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0
        )

        # ⚠️ ChatPromptTemplate은 내부적으로 str.format을 씀
        # JSON 예시의 { } 는 반드시 {{ }} 로 이스케이프해야 KeyError가 안 남.
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a strict judge and synthesizer for a QMS RAG system.\n"
             "You must produce the final answer grounded in the provided evidence.\n\n"
             "CRITICAL RULE (stop infinite loops):\n"
             "- If all evidence is empty (no vector hits AND no SQL rows AND no graph nodes/edges),\n"
             "  set need_more=false and explain that nothing is indexed yet. Suggest uploading PDFs or seeding DB.\n\n"
             "When evidence is insufficient or mismatch BUT there is still something to improve,\n"
             "set need_more=true and propose improve_request.\n\n"
             "Return JSON only with keys: final_answer, need_more, improve_request.\n"
             "Return format example:\n"
             "{{\"final_answer\":\"...\",\"need_more\":false,\"improve_request\":null}}\n\n"
             "CITATION RULES:\n"
             "- If vector hits used, cite like [chunk:123 p:4 score:0.78].\n"
             "- If SQL used, mention template_name and params.\n"
             "- If graph used, mention key nodes/edges and evidence_chunk_ids where available.\n"
            ),
            ("human",
             "User query: {query}\n"
             "Strategy: {strategy}\n"
             "Plan: {plan}\n\n"
             "Vector Hits: {vector_hits}\n\n"
             "Graph Result: {graph_result}\n\n"
             "SQL Result: {sql_result}\n")
        ])

    def _has_any_evidence(self, state: AgentState) -> bool:
        vector_hits: List[Dict[str, Any]] = state.get("vector_hits", []) or []

        sql_result: Dict[str, Any] = state.get("sql_result", {}) or {}
        sql_rows = sql_result.get("rows", []) or []
        # sql_result에 error만 있고 rows가 없을 수도 있음

        graph_result: Dict[str, Any] = state.get("graph_result", {}) or {}
        graph_nodes = graph_result.get("nodes", []) or []
        graph_edges = graph_result.get("edges", []) or []

        return bool(vector_hits) or bool(sql_rows) or bool(graph_nodes) or bool(graph_edges)

    def run(self, state: AgentState) -> AgentState:
        q = state["query"]

        # ✅ 1) 근거가 "완전 0"이면 LLM 호출 자체를 하지 않고 즉시 종료
        if not self._has_any_evidence(state):
            state["final_answer"] = (
                "현재 답변에 사용할 근거(문서/데이터)가 인덱싱되어 있지 않습니다.\n"
                "- 문서 기반 답변이 필요하면: `/files/upload_pdf`로 절차서/CAPA 가이드 PDF를 업로드해 주세요.\n"
                "- 데이터(SQL) 기반 분석이 필요하면: 운영 테이블과 SQL 템플릿을 준비(또는 seed)해 주세요.\n"
                "근거가 준비되면 같은 질문을 다시 해주시면, 인용(citation)과 함께 답변하겠습니다."
            )
            state["need_more"] = False
            state["improve_request"] = "PDF 업로드 또는 SQL 데이터/템플릿 준비"
            return state

        # ✅ 2) 근거가 일부라도 있으면 LLM으로 synthesize + judge
        try:
            res = self.llm.invoke(self.prompt.format_messages(
                query=q,
                strategy=state.get("strategy"),
                plan=state.get("plan"),
                vector_hits=state.get("vector_hits", []),
                graph_result=state.get("graph_result", {}),
                sql_result=state.get("sql_result", {}),
            )).content

            obj = json.loads(res)

            final_answer = obj.get("final_answer", "")
            need_more = bool(obj.get("need_more", False))
            improve_request = obj.get("improve_request", None)

            # ✅ 3) 안전장치: LLM이 이상하게 need_more만 계속 True로 할 수 있으니,
            # evidence가 충분히 없어서 루프가 의미 없을 때 종료시키는 보정
            # (vector_hits=0, sql_rows=0, graph_nodes/edges=0 인 경우는 위에서 걸러졌지만,
            # 혹시 빈 값이 들어와도 방지)
            if not self._has_any_evidence(state):
                need_more = False
                if not final_answer:
                    final_answer = (
                        "현재 근거가 부족하여 답변을 확정할 수 없습니다. "
                        "문서를 업로드하거나 데이터(SQL)를 준비한 뒤 다시 질문해 주세요."
                    )
                if improve_request is None:
                    improve_request = "PDF 업로드 또는 SQL 데이터/템플릿 준비"

        except Exception:
            # ✅ 4) 파싱 실패/LLM 실패해도 무한루프 유발하지 않게 종료로 처리
            final_answer = (
                "답변 생성 중 오류가 발생했거나, 모델 응답을 JSON으로 해석하지 못했습니다.\n"
                "하지만 현재 확보된 근거만으로는 추가 보강 루프를 자동 진행하기 어렵습니다.\n"
                "문서 업로드(PDF) 또는 SQL 데이터 준비 후 다시 시도해 주세요."
            )
            need_more = False
            improve_request = "PDF 업로드 또는 SQL 데이터/템플릿 준비"

        state["final_answer"] = final_answer
        state["need_more"] = need_more
        state["improve_request"] = improve_request
        return state