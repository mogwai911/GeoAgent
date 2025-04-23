from jinja2 import Template

FILE_SEARCH_PROMPT = Template("""
You are a GIS intelligent assistant responsible for selecting relevant files from the geographic data files available in the system, based on the user's data processing task.

Task Description:
{{ question }}

Below is a structured list of all available geographic data files in the system:

{{ metadata }}

📤 Output Requirements:
- Return only a standard Python list
- Each item should be a complete file path, formatted as follows:
```Filepaths
["Full file path1", "Full file path2"]
```
- Strictly follow the above format, **do not add any additional explanations or text**.
""")

CODE_GENERATION_PROMPT = Template("""
  You are a GIS expert tasked with evaluating the effectiveness of retrieved context and the accuracy of generated PyQGIS code for a specific user query.

  Please assess the following aspects:

  1. **Context Relevance**: Evaluate whether the retrieved context is directly related to the user's query.

  2. **Context Coverage**: Determine if the context comprehensively covers the information needed to accomplish the task.

  3. **Code Accuracy**: Assess whether the generated code correctly implements the user's requirements.

  4. **Code-Context Consistency**: Check if the code effectively utilizes the provided context information.

  ---

  **User Query**:
  {{ query }}

  **File Metadata**:
  {{ file_metadata }}

  **Retrieved Context**:
  {{ context }}

  **Generated Code**:
  {{ generated_code }}

  ---

  Please provide your evaluation in the following JSON format:

  ```json
  {
    "context_relevance": {
      "score": 0.0,
      "reasoning": ""
    },
    "context_coverage": {
      "score": 0.0,
      "reasoning": ""
    },
    "code_accuracy": {
      "score": 0.0,
      "reasoning": ""
    },
    "code_context_consistency": {
      "score": 0.0,
      "reasoning": ""
    }
  }
  
  Each score should be a float between 0 and 1, where 1 indicates perfect performance. Provide detailed reasoning for each score.                              
""")

DEBUG_CARE_PROMPT = Template("""
  You are a PyQGIS debugging expert.

  You will receive a failed code execution trace along with:
  - The user's original task description: {{ question }}
  - Structured metadata about the input geospatial file: {{ file_metadata }}
  - Retrieved technical documentation context: {{ context }}
  - The full code that was generated and executed: {{ generated_code }}
  - The full error message raised during execution: {{ code_error }}

  Your task is to analyze the error and produce two types of actionable advice:

  ---

  🔧 CODE_CORRECTION_ADVICE:
  Give direct suggestions on how to fix or regenerate the PyQGIS code.
  You may reference API function names, missing arguments, incorrect types, or logical errors.
  Be specific. If you suspect a module or parameter mismatch (e.g., vector layer used with raster function), point it out.

  🧠 AGENT_CALLING_ADVICE:
  If fixing the code alone is not enough, recommend which agent should be called again and why:
  - If documentation was insufficient → recommend `rag_expert`
  - If the wrong input file was selected → recommend `file_search_expert`
  - If the code just needs to be retried with your fix → recommend `code_generation_expert`

  ---

  📦 Output Format:
  Return both advice blocks **inside markdown code blocks** using the following tags:

  ```CODE_ADVICE
  <your suggestion for code correction>
  ```
                             
  ```AGENT_CALLING_ADVICE
  <your suggestion for what agent should be re-invoked, and why>
  ```  
Be concise, actionable, and only output the two blocks above. Do not explain anything outside the code blocks.            
""")

EVAL_DOCTOR_TEMPLATE = Template("""
You are a GIS expert tasked with evaluating the effectiveness of retrieved context and the accuracy of generated PyQGIS code for a specific user query.

Please assess the following aspects:

1. **Context Relevance**: Evaluate whether the retrieved context is directly related to the user's query.

2. **Context Coverage**: Determine if the context comprehensively covers the information needed to accomplish the task.

3. **Code Accuracy**: Assess whether the generated code correctly implements the user's requirements.

4. **Code-Context Consistency**: Check if the code effectively utilizes the provided context information.

---

**User Query**:
{{ query }}

**File Metadata**:
{{ file_metadata }}

**Retrieved Context**:
{{ context }}

**Generated Code**:
{{ generated_code }}

---

Please provide your evaluation in the following JSON format:

```json
{
  "context_relevance": {
    "score": 0.0,
    "reasoning": ""
  },
  "context_coverage": {
    "score": 0.0,
    "reasoning": ""
  },
  "code_accuracy": {
    "score": 0.0,
    "reasoning": ""
  },
  "code_context_consistency": {
    "score": 0.0,
    "reasoning": ""
  }
}

Each score should be a float between 0 and 1, where 1 indicates perfect performance. Provide detailed reasoning for each score.                                                            
""")












