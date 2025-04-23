
import json
import numpy as np
import faiss
from typing import List, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from sentence_transformers import SentenceTransformer

# === Configuration ===
FAISS_INDEX_PATH = r"/home/kaiyuan/Project_K/rag_db/rag_faiss.index"
METADATA_PATH = r"/home/kaiyuan/Project_K/rag_db/rag_metadata.json"
MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"

# === Load Embedding Model and Vector DB ===
embedding_model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
index = faiss.read_index(FAISS_INDEX_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# === Input and Output Schema ===
class RAGContextInput(BaseModel):
    question: str = Field(..., description="The user's task description or the rewritten query used to retrieve helpful context. This query should focus on retrieving documents that can assist in solving the user's task.")
    top_k: int = Field(8, description="Number of top documents to retrieve from the knowledge base")

class ContextChunk(BaseModel):
    source: str
    title: str
    content: str

class RAGContextOutput(BaseModel):
    context: List[ContextChunk] = Field(..., description="Top matching knowledge base chunks")


# === Main Retrieval Function ===
@tool(
    "rag_context_tool",
    args_schema=RAGContextInput,
    return_direct=False,
    description="Retrieve relevant paragraphs from the knowledge base to support the user's GIS-related task."
)
def query_context(
    question: str,
    # state: Annotated[dict, InjectedState],
    # call_id: Annotated[str, InjectedToolCallId],
    top_k: int = 8
    ) -> RAGContextOutput:
    #print(f"🔍 [rag_context] Entering semantic_rag_context... Call ID: {call_id}")

    query_embedding = embedding_model.encode([question], convert_to_numpy=True)
    distances, indices = index.search(np.array(query_embedding), top_k)

    results = []
    for i in range(top_k):
        idx = indices[0][i]
        if idx < len(metadata):
            item = metadata[idx]
            results.append(ContextChunk(
                source=item.get("file", "Unknown File"),
                title=item.get("title", "No Title"),
                content=item.get("text", "")
            ))
    
    return RAGContextOutput(context=results)

