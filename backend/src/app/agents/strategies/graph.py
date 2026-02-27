from sqlmodel import Session
from app.agents.strategies.base import Strategy
from app.agents.state import AgentState, RetrievalResult
from app.graph.retrieval.subgraph import SubgraphRetriever


class GraphStrategy(Strategy):
    key = "graph"

    def __init__(self):
        self.retriever = SubgraphRetriever(max_seeds=10, max_edges=300)

    def run(self, session: Session, state: AgentState, **kwargs) -> RetrievalResult:
        hops = int(kwargs.get("hops") or 2)

        sg = self.retriever.retrieve(
            session=session,
            query=state.query_normalized,
            hops=hops,
        )

        payload = {
            "hits": [
                {
                    "node_id": h.node_id,
                    "label": h.label,
                    "score": h.score,
                    "reason": h.reason,
                }
                for h in sg.hits
            ],
            "nodes": sg.nodes,
            "edges": sg.edges,
        }

        return RetrievalResult(
            kind="graph",
            payload=payload,
            citations=[],
        )