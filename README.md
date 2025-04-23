# 🧠 GIS Multi-Agent System

A LangGraph-based multi-agent system that performs intelligent GIS data extraction and PyQGIS code generation from natural language instructions.

---

## 🚀 Overview

This project allows users to query GIS datasets using natural language, and automates:

1. **File selection** using semantic search over local metadata.
2. **Technical context retrieval** from a RAG knowledge base.
3. **PyQGIS code generation and execution**.
4. **Failure recovery** with a debug agent.
5. **Evaluation** of task success with structured metrics.

All components are coordinated by a Supervisor Agent managing five tool-using sub-agents.

---

## 🧠 Agent Architecture

### 🧩 Supervisor Agent
Coordinates the workflow:
- File selection → RAG → Code generation → (Debug if failed) → Evaluation

### 🧩 Sub-Agents and Tools

| Agent                | Tool              | Function                                                                 |
|---------------------|-------------------|--------------------------------------------------------------------------|
| `file_search_expert`| `file_search_tool`| Selects geospatial data files via semantic metadata matching             |
| `rag_expert`        | `rag_context_tool`| Retrieves relevant PyQGIS documentation and usage examples               |
| `code_generation_expert`| `code_generate_tool`| Generates and executes PyQGIS code using context + file paths          |
| `debug_expert`      | `debug_care_tool` | Analyzes code errors, suggests corrections and agent re-calls            |
| `evaluation_expert` | `eval_doctor`     | Evaluates solution quality via LLM + embedding similarity                |

---

## 🧠 Project Structure

```bash
.
├── main.py                  # CLI entry point
├── supversior.py           # Supervisor + agent definitions
├── code_runner.py          # Code generation and execution tool
├── debug_care.py           # Debug analysis tool
├── eval_doctor.py          # Evaluation and scoring tool
├── file_search.py          # Metadata-based file retrieval tool
├── rag_context.py          # FAISS-based document retriever
├── model_config.py         # VLLM model config (Qwen72B)
├── prompts/
│   ├── agent_prompt_templates.py
│   └── tool_prompt_templates.py
```

---

## 🧪 How It Works

1. **User input:**  
   Provide a natural language task (e.g., _"Extract all roads longer than 2km and save as GeoJSON."_)

2. **Agent pipeline:**  
   Supervisor invokes a fixed agent sequence, conditionally retrying failed steps.

3. **Execution output:**  
   Results are saved under `/runs/` with:
   - `result.json` – final structured result
   - `messages.txt` – agent message history
   - actual output file (GeoJSON, SHP, etc.)

---

## 💻 Usage

### ⚙️ Prerequisites

- Python 3.9+
- Conda environment (with `PyQGIS`, `faiss`, `langchain`, etc.)
- Local FAISS index and `geo_metadata.json` available under `/Project_K/`
- Running VLLM server for `Qwen72B` model (`qwen_ip.txt` must exist)

### 🟢 Run the System

```bash
python main.py
```

### 🧪 Example Interaction

```shell
[User] > Extract buildings larger than 100sqm in the downtown area and save as SHP.

🧠 Running Agent Workflow...
🔁 Step 1: file_search_expert → ✅
🔁 Step 2: rag_expert → ✅
🔁 Step 3: code_generation_expert → ✅
🔁 Step 4: evaluation_expert → ✅

✅ Execution complete in 9.52s
```

---

## 📦 Output Format

The final JSON result includes:

```json
{
  "user_query": "...",
  "used_file_metadata": { ... },
  "used_context": [ ... ],
  "generated_code": "...",
  "output_path": "...",
  "evaluation": {
    "context_relevance": { "score": ..., "reasoning": "..." },
    "context_coverage": { "score": ..., "reasoning": "..." },
    "code_accuracy": { "score": ..., "reasoning": "..." },
    "code_context_consistency": { "score": ..., "reasoning": "..." },
    "similarity": {
      "context_to_code": ...,
      "full_task_to_code": ...
    }
  }
}
```

---

## 🧠 Model

- 🧠 LLM: [Qwen2.5-72B-Instruct-AWQ] via OpenAI-compatible VLLM endpoint, [gpt-4o-mini] via OpenAI API
- 📚 RAG: [nomic-ai/nomic-embed-text-v2-moe](https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe)

---

## 📁 Data Layout

```bash
/home/kaiyuan/
├── Project_K/
│   ├── data/geo_metadata.json
│   ├── rag_db/rag_faiss.index
│   └── rag_db/rag_metadata.json
└── sp_group/
    ├── result/          # PyQGIS output files
    └── runs/            # Session logs and outputs
```

---

## 🛠️ Troubleshooting

- **No file found?** Check `/Project_K/data/geo_metadata.json`.
- **No context?** Check `/rag_db/rag_metadata.json` and FAISS index.
- **Model not responding?** Ensure `qwen_ip.txt` is present with VLLM IP.

---

## 📜 License

MIT License © 2025 


