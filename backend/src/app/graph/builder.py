# 에이전트 실행 그래프 생성

from langgraph.graph import StateGraph, END # StateGraph: 상태를 들고다니며 노드들을 실행하는 그래프 빌더 클래스, END: 그래프 실행 종료 노드
from src.app.graph.state import AgentState
from src.app.graph import nodes

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("create_run", nodes.create_run) # add_node: 노드 등록
    g.add_node("extract_evidence", nodes.extract_evidence)
    g.add_node("decide_action_agent", nodes.decide_action_agent)
    g.add_node("pick_templates_agent", nodes.pick_templates_agent)
    g.add_node("run_queries", nodes.run_queries)
    g.add_node("judge_quality", nodes.judge_quality)
    g.add_node("adapt_fix", nodes.adapt_fix)
    g.add_node("finalize_answer", nodes.finalize_answer)
    g.add_node("persist_run", nodes.persist_run)

    g.set_entry_point("create_run") # set_entry_point: 시작점 지정
    g.add_edge("create_run", "extract_evidence") # add_edge: 엣지 연결
    g.add_edge("extract_evidence", "decide_action_agent")

    def route_action(state: AgentState):
        return state.get("action", "reject") # state에서 action 값을 꺼내고 없으면 reject 반환

    g.add_conditional_edges( # 조건 분기
        "decide_action_agent", # 출발분기에 해당, decide_action_agent 노드 실행 후 state에 변경사항 저장
        route_action,
        {   # route_action 값에 따라 다음 노드(값에 해당하는 노드)를 실행한다. 
            "db_lookup": "pick_templates_agent",
            "ask_user": END,
            "reject": END,
        },
    )

    g.add_edge("pick_templates_agent", "run_queries")
    g.add_edge("run_queries", "judge_quality")

    def route_quality(state: AgentState):
        return state.get("next_fix", "finalize")

    g.add_conditional_edges(
        "judge_quality",
        route_quality,
        {
            "add_queries": "adapt_fix",
            "refine_params": "adapt_fix",
            "ask_user": END,
            "finalize": "finalize_answer",
        },
    )

    g.add_edge("adapt_fix", "pick_templates_agent")  # 보강 후 다시 선택/실행
    g.add_edge("finalize_answer", "persist_run")
    g.add_edge("persist_run", END)

    return g.compile() # 설계도처럼 연결해둔 그래프를 실제 실행 가능한 형태로 검파일하여 반환