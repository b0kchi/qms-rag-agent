from typing import TypedDict, List, Dict, Any, Optional, Literal
from langchain_core.messages import BaseMessage

Strategy = Literal["VECTOR", "GRAPH", "SQL", "HYBRID"]

class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]

    query: str

    # Router output
    strategy: Strategy
    plan: List[str]  # e.g. ["SQL", "VECTOR", "JUDGE"]
    rationale: str

    # Inputs/Signals
    hints: Dict[str, Any]  # detected entities, has_numbers, etc.

    # Vector results
    vector_hits: List[Dict[str, Any]]   # {chunk_id, score, text, file_id, source_page}

    # Graph results
    graph_result: Dict[str, Any]        # {nodes:[...], edges:[...], explanation:str}

    # SQL results
    sql_result: Dict[str, Any]          # {template_name, params, rows:[...], summary:str}

    # Judge
    final_answer: str
    need_more: bool
    improve_request: Optional[str]
    loop_count: int