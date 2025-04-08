# ✅ agent_graph.py — Automatic Pipeline version of LangGraph Agent (use RunnableLambda wrapper to avoid ToolNode errors)

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from agent.tools.file_search import query_to_file, FileSearchInput
from agent.tools.rag_context import query_context, RAGContextInput
from agent.tools.code_runner import code_generate_and_debug, CodeRunnerInput
from agent.memory.checkpoint import MemorySaver

# ✅ Use dict state structure to be compatible with missing initial fields
def build_agent_graph():
    workflow = StateGraph(dict)

    # ✅ Node 1: File Search
    search_node = RunnableLambda(lambda state: {
        **state,
        "filepaths": query_to_file(FileSearchInput(question=state["question"])).filepaths
    })

    # ✅ Node 2: Semantic Context Retrieval
    context_node = RunnableLambda(lambda state: {
        **state,
        "context": query_context(RAGContextInput(question=state["question"], top_k=5)).context
    })

    # ✅ Node 3: Code Generation + Execution + Error Tracking
    code_node = RunnableLambda(lambda state: {
        **state,
        **code_generate_and_debug(CodeRunnerInput(
            question=state["question"],
            context=state["context"],
            filepaths=state["filepaths"],
            output_path=state["output_path"],
            history=state.get("history", [])
        )).dict()
    })

    # ✅ Building the graph structure
    workflow.add_node("file_search", search_node)
    workflow.add_node("rag_context", context_node)
    workflow.add_node("code_runner", code_node)

    workflow.set_entry_point("file_search")
    workflow.add_edge("file_search", "rag_context")
    workflow.add_edge("rag_context", "code_runner")
    workflow.add_edge("code_runner", END)

    checkpoint_saver = MemorySaver("/home/kaiyuan/Downloads/agent_output")
    return workflow.compile().with_config({"checkpoint": checkpoint_saver, "debug": True})

