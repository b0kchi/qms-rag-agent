from __future__ import annotations

import json
from dataclasses import dataclass, field
from collections import deque
from sqlmodel import Session

from app.com.repositories.graph_repo import GraphRepo
from app.com.utils.text import extract_keywords


@dataclass
class GraphHit:
    node_id: str
    label: str
    score: float
    reason: str = ""


@dataclass
class Subgraph:
    """
    검색 결과로 반환할 서브그래프 구조
    """
    nodes: dict[str, dict] = field(default_factory=dict)  # node_id -> {"label": str, "props": dict}
    edges: list[dict] = field(default_factory=list)       # {"id","src_id","dst_id","rel","props"}
    hits: list[GraphHit] = field(default_factory=list)    # 상위 매칭 노드들


def _safe_json(s: str | None) -> dict:
    if not s:
        return {}
    try:
        v = json.loads(s)
        return v if isinstance(v, dict) else {"value": v}
    except Exception:
        return {"raw": s}


def _score_label(label: str, query: str) -> tuple[float, str]:
    """
    MVP 스코어링:
    - 질의 키워드가 node.label에 포함되면 점수 상승
    """
    kws = extract_keywords(query, max_n=12)
    if not kws:
        return 0.1, "no keywords"

    ll = (label or "").lower()
    hit = [k for k in kws if k.lower() in ll]
    score = 0.1 + 0.9 * (len(hit) / max(1, len(kws)))
    return score, f"label keyword hits: {hit}"


class SubgraphRetriever:
    """
    최소 Graph 검색기(Neo4j 없이, GraphNode/GraphEdge 테이블 기반)

    알고리즘:
    1) 질의 키워드 추출
    2) keyword LIKE 로 seed node 후보 검색
    3) seed에서 k-hop(BFS) 확장해 서브그래프 구성
    4) node label 매칭 기반으로 hits 생성
    """

    def __init__(self, max_seeds: int = 10, max_edges: int = 300, neighbor_limit: int = 500):
        self.max_seeds = max_seeds
        self.max_edges = max_edges
        self.neighbor_limit = neighbor_limit

    def retrieve(self, session: Session, query: str, hops: int = 2) -> Subgraph:
        repo = GraphRepo(session)

        # 1) 키워드 추출
        kws = extract_keywords(query, max_n=8)

        # 2) seed node 검색 (label LIKE)
        seeds = []
        for k in kws:
            seeds.extend(repo.search_nodes_by_label_like(k, limit=10))
            if len(seeds) >= self.max_seeds:
                break

        # seed가 없으면: fallback으로 query 자체로 한번 더
        if not seeds and query.strip():
            seeds = repo.search_nodes_by_label_like(query.strip()[:30], limit=self.max_seeds)

        # 중복 제거
        uniq = {}
        for n in seeds:
            uniq[n.id] = n
        seeds = list(uniq.values())[: self.max_seeds]

        sg = Subgraph()

        # seed 노드 저장
        for n in seeds:
            sg.nodes[n.id] = {"label": n.label, "props": _safe_json(n.props_json)}

        # 3) k-hop 확장(BFS)
        # frontier: 현재 hop에서 확장할 노드들
        frontier = deque([n.id for n in seeds])
        visited = set([n.id for n in seeds])

        current_hop = 0
        # hop별로 frontier를 구분하려면 레벨 트래킹
        level_end_count = len(frontier)

        while frontier and current_hop < max(0, hops):
            node_ids = list(frontier)
            # 현재 frontier를 다 비우고 이 레벨의 이웃을 추가하는 방식
            frontier.clear()

            edges = repo.neighbors(node_ids, limit=self.neighbor_limit)
            for e in edges:
                if len(sg.edges) >= self.max_edges:
                    break

                sg.edges.append({
                    "id": e.id,
                    "src_id": e.src_id,
                    "dst_id": e.dst_id,
                    "rel": e.rel,
                    "props": _safe_json(e.props_json),
                })

                # 양끝 노드를 sg.nodes에 추가
                for nid in (e.src_id, e.dst_id):
                    if nid not in sg.nodes:
                        node = repo.get_node(nid)
                        if node:
                            sg.nodes[nid] = {"label": node.label, "props": _safe_json(node.props_json)}
                    if nid not in visited:
                        visited.add(nid)
                        frontier.append(nid)

            current_hop += 1

        # 4) hits 생성(노드 스코어링)
        hits: list[GraphHit] = []
        for node_id, data in sg.nodes.items():
            s, reason = _score_label(str(data.get("label", "")), query)
            hits.append(GraphHit(node_id=node_id, label=str(data.get("label", "")), score=s, reason=reason))

        hits.sort(key=lambda x: x.score, reverse=True)
        sg.hits = hits[:20]

        return sg