import json
import re
import os
from typing import List, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langchain_openai import ChatOpenAI
from prompts.tool_prompt_templates import DEBUG_CARE_PROMPT
from config.model_config import get_model_config
from langchain_core.messages.ai import AIMessage

# === LLM config ===
model_config = get_model_config()
model = ChatOpenAI(
    base_url=model_config['base_url'],
    api_key=model_config['api_key'],
    model_name=model_config['model_name'],
    streaming=True)

class DebugInput(BaseModel):
    question: str = Field(..., description="User's task description")
    context: str = Field(..., description="RAG retrieved technical documentation context")
    file_metadata: str = Field(..., description="Metadata of the file used by code agent")
    generated_code: str = Field(..., description="Generated code by code agent")
    code_error: str = Field(..., description="Generated code error by code agent")

class AnalysisChunk(BaseModel):
    code_correction_advice: str
    agent_calling_advice: str


class DebugOutput(BaseModel):
    context: List[AnalysisChunk] = Field(..., description="Advice of code correction and agent calling")

@tool(
    "debug_care_tool",
    args_schema=DebugInput,
    return_direct=False,
    description="Analyze code errors and return structured suggestions for code correction and potential agent re-invocation based on context, metadata, and execution traceback."
)
def debug_care(
    question: str,
    context: str,
    file_metadata: str,
    generated_code: str,
    code_error: str,
    # state: Annotated[dict, InjectedState],
    # call_id: Annotated[str, InjectedToolCallId]
    ) -> DebugOutput:
    #print(f"[debug_care] Entering debug_care... Call ID: {call_id}")

    
    prompt = DEBUG_CARE_PROMPT.render(
        question=question,
        file_metadata=file_metadata,
        context=context,
        generated_code=generated_code,
        code_error=code_error
    )

    raw_output = model.invoke(prompt)

    if isinstance(raw_output, AIMessage):
        raw_output = raw_output.content or ""
    elif not isinstance(raw_output, str):
        raw_output = str(raw_output or "")

    match_code = re.search(r"```CODE_ADVICE\s*(.*?)```", raw_output, re.DOTALL)
    match_agent = re.search(r"```AGENT_CALLING_ADVICE\s*(.*?)```", raw_output, re.DOTALL)

    generated_code_advice = match_code.group(1).strip() if match_code else "No correction advice found."
    generated_agent_advice = match_agent.group(1).strip() if match_agent else "No agent calling advice found."


    results = []
    results.append(AnalysisChunk(
        code_correction_advice=generated_code_advice,
        agent_calling_advice=generated_agent_advice
    ))
       
    return DebugOutput(context=results)
