import os
import re
import json
import tempfile
import subprocess
import traceback
from typing import List
from pydantic import BaseModel, Field
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from agent.prompts.prompt_templates import CODE_GENERATION_PROMPT
from agent.tools.llm_client import QwenChat
from langchain_core.messages.ai import AIMessage

class CodeRunnerInput(BaseModel):
    question: str = Field(..., description="User's task description")
    context: str = Field(..., description="RAG retrieved technical documentation context")
    filepaths: List[str] = Field(..., description="List of input data file paths")
    output_path: str = Field(..., description="Directory to save output results")
    history: List[dict] = Field(default_factory=list, description="History of previous failed code attempts")

class CodeRunnerOutput(BaseModel):
    code: str
    output_file: str
    success: bool
    error: str = ""
    stdout: str = ""
    stderr: str = ""
    history: List[dict] = Field(default_factory=list)

def code_generate_and_debug(input: CodeRunnerInput) -> CodeRunnerOutput:
    print("\U0001f9e0 [code_runner] Entering code_generate_and_debug...")
    question = input.question
    context = input.context
    filepaths = input.filepaths
    output_dir = input.output_path
    history = input.history or []
    error = None
    generated_code = ""
    stdout = ""
    stderr = ""

    for attempt in range(5):
        prompt = CODE_GENERATION_PROMPT.render(
            question=question,
            filepath="\n".join(filepaths),
            context=context,
            error=error,
            history=history,
            output_path=output_dir
        )

        llm = QwenChat()
        raw_output = llm.invoke(prompt)

        if isinstance(raw_output, AIMessage):
            raw_output = raw_output.content or ""
        elif not isinstance(raw_output, str):
            raw_output = str(raw_output or "")

        match = re.search(r"```python\s*(.*?)```", raw_output, re.DOTALL)
        generated_code = match.group(1).strip() if match else raw_output.strip()

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
                timeout=60,
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

            history.append({
                "code": generated_code,
                "error": "" if success else (stderr or "Generated code failed to save a valid output file."),
                "stdout": stdout,
                "stderr": stderr,
                "output_file": output_file
            })

            if success:
                return CodeRunnerOutput(
                    code=generated_code,
                    output_file=output_file,
                    success=True,
                    stdout=stdout,
                    stderr=stderr,
                    history=history
                )

            error = stderr or "Generated code failed to save a valid output file."

        except Exception as e:
            tb = traceback.format_exc()
            error_msg = f"{str(e)}\nTraceback:\n{tb}"
            history.append({
                "code": generated_code,
                "error": error_msg,
                "stdout": stdout,
                "stderr": stderr or tb,
                "output_file": ""
            })
            error = error_msg

        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    return CodeRunnerOutput(
        code=generated_code,
        output_file="",
        success=False,
        error=error or "Execution failed",
        stdout=stdout,
        stderr=stderr,
        history=history
    )
