from sqlmodel import Session, select
from app.schema.models.graph_node import GraphNode
from app.schema.models.graph_edge import GraphEdge


class GraphRepo:
    """
    GraphNode / GraphEdge 테이블 기반
    간단 그래프 접근 레이어
    """

    def __init__(self, session: Session):
        self.session = session

    # =========================
    # Node 관련
    # =========================

    def upsert_node(self, node: GraphNode) -> None:
        """
        node.id 기준 upsert
        """
        existing = self.session.get(GraphNode, node.id)

        if existing:
            existing.label = node.label
            existing.props_json = node.props_json
        else:
            self.session.add(node)

        self.session.commit()

    def get_node(self, node_id: str) -> GraphNode | None:
        return self.session.get(GraphNode, node_id)

    def search_nodes_by_label_like(self, term: str, limit: int = 20) -> list[GraphNode]:
        """
        label LIKE 검색 (대소문자 무시)
        운영에서는 pg_trgm + GIN 인덱스 추천
        """
        if not term:
            return []

        stmt = (
            select(GraphNode)
            .where(GraphNode.label.ilike(f"%{term}%"))
            .limit(limit)
        )

        return list(self.session.exec(stmt).all())

    def list_nodes(self, limit: int = 100) -> list[GraphNode]:
        stmt = select(GraphNode).limit(limit)
        return list(self.session.exec(stmt).all())

    # =========================
    # Edge 관련
    # =========================

    def add_edge(self, edge: GraphEdge) -> None:
        """
        edge.id 기준 중복 방지
        """
        existing = self.session.get(GraphEdge, edge.id)
        if not existing:
            self.session.add(edge)
            self.session.commit()

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        return self.session.get(GraphEdge, edge_id)

    def neighbors(self, node_ids: list[str], limit: int = 200) -> list[GraphEdge]:
        """
        주어진 node_ids에 연결된 edge 조회
        (src 또는 dst가 포함된 edge)
        """
        if not node_ids:
            return []

        stmt = (
            select(GraphEdge)
            .where(
                (GraphEdge.src_id.in_(node_ids))
                | (GraphEdge.dst_id.in_(node_ids))
            )
            .limit(limit)
        )

        return list(self.session.exec(stmt).all())

    def list_edges(self, limit: int = 200) -> list[GraphEdge]:
        stmt = select(GraphEdge).limit(limit)
        return list(self.session.exec(stmt).all())