from typing import List, Optional
from sqlmodel import Session, select
from app.models.graph_models import GraphNode, GraphEdge

class GraphRepo:
    def __init__(self, session: Session):
        self.session = session

    def find_nodes_by_names(self, names: List[str]) -> List[GraphNode]:
        if not names:
            return []
        stmt = select(GraphNode).where(GraphNode.name.in_(names))
        return list(self.session.exec(stmt))

    def get_neighbors(self, node_ids: List[int], max_hops: int = 1) -> dict:
        """
        아주 단순한 hop 확장 (BFS 유사)
        반환: {nodes: [...], edges: [...]}
        """
        visited = set(node_ids)
        frontier = set(node_ids)

        all_nodes = []
        all_edges = []

        for _ in range(max_hops):
            if not frontier:
                break
            ids = list(frontier)
            frontier = set()

            edges_stmt = select(GraphEdge).where(
                (GraphEdge.src_node_id.in_(ids)) | (GraphEdge.dst_node_id.in_(ids))
            )
            edges = list(self.session.exec(edges_stmt))
            all_edges.extend(edges)

            next_node_ids = set()
            for e in edges:
                next_node_ids.add(e.src_node_id)
                next_node_ids.add(e.dst_node_id)

            new_ids = next_node_ids - visited
            visited |= new_ids
            frontier |= new_ids

        if visited:
            nodes_stmt = select(GraphNode).where(GraphNode.id.in_(list(visited)))
            all_nodes = list(self.session.exec(nodes_stmt))

        return {
            "nodes": all_nodes,
            "edges": all_edges
        }