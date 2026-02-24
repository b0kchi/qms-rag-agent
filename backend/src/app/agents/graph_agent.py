import re
from sqlmodel import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.repositories.graph_repo import GraphRepo
from app.agents.state import AgentState


class GraphRetrievalAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0,
        )

        self.extract_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Extract entity names from the query for graph search.\n"
             "Return JSON only: {entities:[...]} where entities are raw names like LOT_A, EQUIP_01, DEFECT_X.\n"
             "If none, return {entities:[]}"),
            ("human", "{query}")
        ])

    def _simple_extract(self, q: str) -> list[str]:
        pats = [
            r"\bLOT[_-]?[A-Z0-9]+\b",
            r"\b(EQP|EQUIP)[_-]?[A-Z0-9]+\b",
            r"\bDEFECT[_-]?[A-Z0-9]+\b",
            r"\bLINE[_-]?[A-Z0-9]+\b",
        ]
        found = set()
        for p in pats:
            for m in re.findall(p, q, flags=re.IGNORECASE):
                if isinstance(m, tuple):
                    continue
                found.add(m)
        return list(found)

    def run(self, session: Session, state: AgentState) -> AgentState:
        q = state["query"]
        repo = GraphRepo(session)

        entities = self._simple_extract(q)

        # regex로 못 찾았으면 LLM으로 보강
        if not entities:
            try:
                import json
                res = self.llm.invoke(self.extract_prompt.format_messages(query=q)).content
                obj = json.loads(res)
                entities = obj.get("entities", []) or []
            except Exception:
                entities = []

        nodes = repo.find_nodes_by_names(entities)
        node_ids = [n.id for n in nodes if n.id is not None]

        sub = repo.get_neighbors(node_ids, max_hops=2) if node_ids else {"nodes": [], "edges": []}

        # 설명 생성
        explain_prompt = ChatPromptTemplate.from_messages([
            ("system", "Explain why these graph nodes/edges matter for answering the query. Be concise."),
            ("human", "Query: {q}\nNodes: {nodes}\nEdges: {edges}\n")
        ])
        try:
            explanation = self.llm.invoke(explain_prompt.format_messages(
                q=q,
                nodes=[{"id": n.id, "label": n.label, "name": n.name} for n in sub["nodes"]],
                edges=[{"src": e.src_node_id, "rel": e.relation, "dst": e.dst_node_id, "w": e.weight, "chunk": e.evidence_chunk_id} for e in sub["edges"]],
            )).content
        except Exception:
            explanation = "Graph explanation unavailable."

        state["graph_result"] = {
            "entities": entities,
            "nodes": [{"id": n.id, "label": n.label, "name": n.name} for n in sub["nodes"]],
            "edges": [{"id": e.id, "src": e.src_node_id, "dst": e.dst_node_id, "relation": e.relation, "weight": e.weight, "evidence_chunk_id": e.evidence_chunk_id} for e in sub["edges"]],
            "explanation": explanation,
        }
        return state