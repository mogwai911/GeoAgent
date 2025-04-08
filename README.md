# GIS Code Generation Agent Pipeline Overview

This document outlines the architecture and operational flow of the GIS Code Generation Agent, which is built as a modular, self-correcting agent system capable of interpreting user queries, generating PyQGIS code, executing it, and automatically debugging failures.

## 🧠 Core Objective
Automate geospatial data extraction from natural language queries using a pipeline that incorporates:

1. **Semantic File Selection (file_search)**
2. **Contextual Documentation Retrieval (rag_context)**
3. **Code Generation + Debugging Loop (code_runner)**

---

## 🔧 Main Components

### 1. **User Query Input**
Users provide a query in natural language, e.g., _"extract the highways where highway is 'service' and save as GeoJSON"_.

### 2. **File Search Tool**
Selects relevant GIS data files using semantic understanding and indexed metadata.
- Output: list of relevant `filepaths`

### 3. **RAG Context Tool**
Retrieves documentation passages from a QGIS technical knowledge base.
- Uses rewritten, tool-specific semantic queries
- Output: `context` string for grounding code generation

### 4. **Code Runner (Self-Healing Loop)**
This component is a full agent on its own:
- Uses structured prompt templating (Jinja2)
- Invokes `QwenChat` to generate Python code
- Saves code to a temporary file and executes via `subprocess`
- Parses result from `stdout` (uses `##RESULT##` tag)
- Automatically retries up to 5 times if the code fails
- Tracks all attempts in a `history` object used for refinement

---

## 🔁 Retry & Memory Logic (CodeRunner)
```python
for attempt in range(5):
    # Prompt generation with context, history, and error
    # LLM code generation
    # Execute code and check output_file
    # If valid file produced: return
    # Else: append to history and retry with updated context
```

The retry logic allows the agent to learn from past failures and fix common issues such as:
- Missing imports
- Wrong method names (e.g., `writeVectorLayer` → `writeAsVectorFormatV3`)
- Incorrect output file paths

---

## 🧾 Output Format
On successful execution, the agent extracts:
- `output_file`: actual result file (e.g., `.geojson`, `.shp`, etc.)
- `stdout`, `stderr`, and `error` (if any)
- Full `history` of attempts

---

## 📂 File Path Awareness
All output is saved to the user-specified directory:
```python
output_path = os.path.join(output_dir, "filtered_highways.geojson")
```

This logic is enforced via prompt instructions:
> 💾 Save the resulting files **under this exact directory** (not hardcoded elsewhere). You can choose the filename and extension based on the task.

---

## ✅ Agent Characteristics
- **Autonomous & Recoverable**: self-healing via multi-step retry
- **Memory-enhanced**: each attempt is recorded and used for improvement
- **Modularized**: clear separation of file selection, knowledge retrieval, and code execution
- **Language-driven**: all components driven by natural language semantics

---

## 📍 Future Enhancements
- Add explicit reasoning steps (Plan → Code → Execute → Reflect)
- Support multi-file inputs and complex spatial analysis workflows
- Improve rag_context with citation-traceable evidence
- Add tool-use logging and interactive feedback control

---

_This architecture demonstrates an end-to-end GIS automation agent capable of translating human intent into structured, verifiable geospatial workflows._

