
import json
import numpy as np
import faiss
from typing import List
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from agent.prompts.prompt_templates import RAG_QUERY_REWRITE_PROMPT
from agent.tools.llm_client import QwenChat

# === Configuration ===
FAISS_INDEX_PATH = "/home/kaiyuan/Project_K/rag_db/rag_faiss.index"
METADATA_PATH = "/home/kaiyuan/Project_K/rag_db/rag_metadata.json"
MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"

# === Load Embedding Model and Vector DB ===
embedding_model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
index = faiss.read_index(FAISS_INDEX_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# === Input and Output Schema ===
class RAGContextInput(BaseModel):
    question: str = Field(..., description="The user's task description")
    top_k: int = Field(8, description="Number of top documents to retrieve from the knowledge base")

class RAGContextOutput(BaseModel):
    context: str = Field(..., description="Context paragraphs retrieved from the knowledge base")

# === Main Retrieval Function ===
def query_context(input: RAGContextInput) -> RAGContextOutput:
    print("📚 [rag_context] Entering semantic_rag_context...")
    original_query = input.question

    # ✅ Use LLM to rewrite query for better semantic retrieval
    llm = QwenChat()
    reformulated = llm.invoke(RAG_QUERY_REWRITE_PROMPT.render(question=original_query))
    if hasattr(reformulated, "content"):
        rewritten_query = reformulated.content.strip()
    else:
        rewritten_query = str(reformulated)

    print(f"🔄 [rag_context] Rewritten Query: {rewritten_query}")

    query_embedding = embedding_model.encode([rewritten_query], convert_to_numpy=True)
    distances, indices = index.search(np.array(query_embedding), input.top_k)

    blocks = []
    for i in range(input.top_k):
        idx = indices[0][i]
        if idx < len(metadata):
            title = metadata[idx].get("title", "No Title")
            text = metadata[idx].get("text", "")
            source = metadata[idx].get("file", "Unknown File")
            blocks.append(f"# Source: {source}\nTitle: {title}\nContent:\n{text}\n---")

    return RAGContextOutput(context="\n\n".join(blocks))

