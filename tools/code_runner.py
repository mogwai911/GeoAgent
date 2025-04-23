import os
import re
import json
import tempfile
import subprocess
import traceback
from typing import List, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langchain_openai import ChatOpenAI
from config.model_config import get_model_config
from prompts.tool_prompt_templates import CODE_GENERATION_PROMPT
from langchain_core.messages.ai import AIMessage

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# === LLM config ===
model_config = get_model_config()
model = ChatOpenAI(
    base_url=model_config['base_url'],
    api_key=model_config['api_key'],
    model_name=model_config['model_name'],
    streaming=True)

class CodeRunnerInput(BaseModel):
    question: str = Field(..., description="User's task description")
    context: str = Field(..., description="RAG retrieved technical documentation context")
    filepaths: List[str] = Field(..., description="List of input data file paths")
    debug_advice: str | None = Field(None, description="Optional debug suggestions for improving the generated code")

class CodeRunnerOutput(BaseModel):
    code: str
    output_file: str
    tool_used_file: str
    success: bool
    stdout: str = ""
    stderr: str = ""

@tool(
    "code_generate_tool",
    args_schema=CodeRunnerInput,
    return_direct=False,
    description="Generate and execute PyQGIS code based on the user task, semantic context, and provided input files. The tool attempts to run the code, capture standard output and error, and determine whether the execution was successful. Optionally accepts debug advice to refine the generation logic."
)
def code_generate(
    question: str,
    context: str,
    filepaths: List[str],
    debug_advice: str | None = None,
    # state: Annotated[dict, InjectedState],
    # call_id: Annotated[str, InjectedToolCallId]
    ) -> CodeRunnerOutput:
    #print(f"[code_runner] Entering code_generate... Call ID: {call_id}")
    generated_code = ""
    stdout = ""
    stderr = ""
    
    prompt = CODE_GENERATION_PROMPT.render(
        question=question,
        filepath=filepaths,
        context=context,
        output_path=r"/home/kaiyuan/lu2025-17-15/Kaiyuan/sp_group/result",
        debug_advice=debug_advice or ""
    )

    raw_output = model.invoke(prompt)

    if isinstance(raw_output, AIMessage):
        raw_output = raw_output.content or ""
    elif not isinstance(raw_output, str):
        raw_output = str(raw_output or "")

    match = re.search(r"```python\s*(.*?)```", raw_output, re.DOTALL)
    generated_code = match.group(1).strip() if match else raw_output.strip()
    match_input = re.search(r"##INPUT##\s*(\{.*\})", generated_code)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_file:
            temp_file.write(generated_code)
            script_path = temp_file.name

        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["PYTHONUNBUFFERED"] = "1"

        result = subprocess.run(
            ["python", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            env=env,
            text=True
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        match_structured = re.search(r"##RESULT##\s*(\{.*\})", stdout)
        try:
            result_data = json.loads(match_structured.group(1)) if match_structured else {}
            output_file = result_data.get("output_file", "")
        except Exception:
            output_file = ""

        file_exists = os.path.exists(output_file)
        file_size_ok = os.path.getsize(output_file) > 0 if file_exists else False
        traceback_error = "traceback" in stderr.lower()

        success = file_exists and file_size_ok and not traceback_error

        if success:
            return CodeRunnerOutput(
                code=generated_code,
                output_file=output_file,
                tool_used_file=match_input,
                success=True,
                stdout=stdout,
                stderr=stderr
            )

    except Exception as e:
        stderr += f"\n[Exception Caught]\n{traceback.format_exc()}"

    finally:
        if os.path.exists(script_path):
            os.remove(script_path)

    return CodeRunnerOutput(
        code=generated_code,
        output_file="",
        tool_used_file=match_input,
        success=False,
        stdout=stdout,
        stderr=stderr

    )
