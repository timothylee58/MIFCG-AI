from functools import lru_cache
from langgraph.graph import StateGraph, END
from .state import RegComplyState
from .nodes import router_node, retriever_node, synthesizer_node


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(RegComplyState)
    g.add_node("router", router_node)
    g.add_node("retriever", retriever_node)
    g.add_node("synthesizer", synthesizer_node)
    g.set_entry_point("router")
    g.add_edge("router", "retriever")
    g.add_edge("retriever", "synthesizer")
    g.add_edge("synthesizer", END)
    return g.compile()


rag_graph = build_graph()
