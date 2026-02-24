from typing import Callable
from sqlmodel import Session
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.router import RouterSupervisor
from app.agents.vector_agent import VectorRetrievalAgent
from app.agents.graph_agent import GraphRetrievalAgent
from app.agents.sql_agent import SQLAnalysisAgent
from app.agents.judge import SynthesizerJudge

router = RouterSupervisor()
vector_agent = VectorRetrievalAgent()
graph_agent = GraphRetrievalAgent()
sql_agent = SQLAnalysisAgent()
judge = SynthesizerJudge()

def make_workflow(get_session: Callable[[], Session]):
    g = StateGraph(AgentState)

    def n_router(state: AgentState) -> AgentState:
        return router.route(state)

    def n_sql(state: AgentState) -> AgentState:
        with get_session() as s:
            return sql_agent.run(s, state)

    def n_vector(state: AgentState) -> AgentState:
        with get_session() as s:
            return vector_agent.run(s, state)

    def n_graph(state: AgentState) -> AgentState:
        with get_session() as s:
            return graph_agent.run(s, state)

    def n_judge(state: AgentState) -> AgentState:
        return judge.run(state)

    g.add_node("ROUTER", n_router)
    g.add_node("SQL", n_sql)
    g.add_node("VECTOR", n_vector)
    g.add_node("GRAPH", n_graph)
    g.add_node("JUDGE", n_judge)

    g.set_entry_point("ROUTER")

    # Router가 만든 plan 순서를 그대로 “강제 실행”하려면, plan interpreter 노드가 필요하지만
    # 처음 버전에서는 전략별 고정 플로우로 간단화한다.

    def route_after_router(state: AgentState):
        st = state.get("strategy")
        if st == "SQL":
            return "SQL"
        if st == "VECTOR":
            return "VECTOR"
        if st == "GRAPH":
            return "GRAPH"
        return "SQL"  # HYBRID 기본은 SQL부터

    g.add_conditional_edges("ROUTER", route_after_router, {
        "SQL": "SQL",
        "VECTOR": "VECTOR",
        "GRAPH": "GRAPH",
    })

    # 각 실행 후 Judge로
    g.add_edge("SQL", "VECTOR")     # HYBRID 대비: SQL → VECTOR
    g.add_edge("VECTOR", "GRAPH")   # HYBRID 대비: VECTOR → GRAPH
    g.add_edge("GRAPH", "JUDGE")

    # VECTOR only / GRAPH only / SQL only도 결국 위 경로 타지만
    # 해당 노드들이 “state에 결과가 없으면 그냥 빈 결과로” Judge가 처리하게 된다.

    # Judge 후 loop
    def after_judge(state: AgentState):
        # loop_count 증가
        cnt = int(state.get("loop_count", 0)) + 1
        state["loop_count"] = cnt

        # 최대 2회까지만 보강 루프 허용
        if state.get("need_more") and cnt <= 2:
            return "ROUTER"
        return END

    g.add_conditional_edges("JUDGE", after_judge, {
        "ROUTER": "ROUTER",
        END: END
    })

    return g.compile()