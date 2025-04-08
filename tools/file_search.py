# tools/file_search.py (LangGraph Agent Tool version)

import json
import re
import os
from typing import List
from pydantic import BaseModel, Field
from langchain.tools import tool
from agent.tools.llm_client import QwenChat
from agent.prompts.prompt_templates import FILE_SEARCH_PROMPT

# === Configuration ===
METADATA_PATH = "/home/kaiyuan/Project_K/data/geo_metadata.json"

# === Structured Output Definition ===
class FileSearchResult(BaseModel):
    filepaths: List[str] = Field(..., description="List of geographic data file paths relevant to the current task")

# === Tool Interface Definition ===
class FileSearchInput(BaseModel):
    question: str = Field(..., description="The user's task request")


def query_to_file(input: FileSearchInput) -> FileSearchResult:
    """
Based on the user's natural language task request, combined with the existing local geographic data metadata, filter all possible related vector or raster file paths.
- Input is a task description string
- Internally call LLM to understand the metadata semantically
- Return a set of recommended file full paths
"""
    print("🔍 [file_search] Entering semantic_file_search...")
    question = input.question

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Construct structured file list string
    formatted_metadata = "\n".join([
        f"- File: {item['path']}\n"
        f"  Type: {item['type']} ({item.get('geometry', '')})\n"
        f"  Fields: {item['fields']}\n"
        f"  Features/Size: {item['features']}\n"
        f"  CRS: {item.get('crs', 'Unknown')}\n"
        f"  Description: {item['description']}\n"
        for item in metadata
    ])

    # Construct prompt
    prompt = FILE_SEARCH_PROMPT.render(
        question=question,
        metadata=formatted_metadata
    )

    llm = QwenChat()
    response = llm.invoke(prompt).content.strip()
    match = re.search(r"```Filepaths\s*\n(.*?)```", response, re.DOTALL)
    if match:
        response_text = match.group(1).strip()
    else:
        response_text = response.strip()

    try:
        filepaths = json.loads(response_text)
    except json.JSONDecodeError:
        filepaths = [response]

    return FileSearchResult(filepaths=filepaths)

