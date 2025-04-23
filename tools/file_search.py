import json
import re
import os
from typing import List, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langchain_openai import ChatOpenAI
from prompts.tool_prompt_templates import FILE_SEARCH_PROMPT
from config.model_config import get_model_config
from langchain_core.messages.ai import AIMessage

# === LLM config ===
model_config = get_model_config()
model = ChatOpenAI(
    base_url=model_config['base_url'],
    api_key=model_config['api_key'],
    model_name=model_config['model_name'],
    streaming=True)

# === Configuration ===
METADATA_PATH = r"/home/kaiyuan/Project_K/data/geo_metadata.json"


# === Output Schema ===
class FileMetadata(BaseModel):
    path: str
    type: str
    geometry: str = ""
    fields: List[str]
    features: int
    crs: str = "Unknown"
    description: str

class FileSearchResult(BaseModel):
    files: List[FileMetadata] = Field(..., description="List of matched geospatial files with full metadata.")

# === Input Schema ===
class FileSearchInput(BaseModel):
    question: str = Field(..., description="User's geospatial task request in natural language")

# === Tool Definition ===
@tool(
    "file_search_tool",
    args_schema=FileSearchInput,
    return_direct=False,
    description="Search local geographic files that are relevant to a given task using semantic matching on metadata."
)
def query_to_file(
    question: str,
    # state: Annotated[dict, InjectedState],
    # call_id: Annotated[str, InjectedToolCallId]
) -> FileSearchResult:
    #print(f"🔍 [file_search] Entering semantic_file_search... Call ID: {call_id}")

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    formatted_metadata = "\n".join([
        f"- File: {item['path']}\n"
        f"  Type: {item['type']} ({item.get('geometry', '')})\n"
        f"  Fields: {item['fields']}\n"
        f"  Features/Size: {item['features']}\n"
        f"  CRS: {item.get('crs', 'Unknown')}\n"
        f"  Description: {item['description']}\n"
        for item in metadata
    ])

    prompt = FILE_SEARCH_PROMPT.render(
        question=question,
        metadata=formatted_metadata
    )

    response = model.invoke(prompt).content.strip()

    if isinstance(response, AIMessage):
        response = response.content or ""
    elif not isinstance(response, str):
        response = str(response or "")

    match = re.search(r"```Filepaths\s*\n(.*?)```", response, re.DOTALL)
    if match:
        response_text = match.group(1).strip()
    else:
        response_text = response.strip()

    try:
        selected_paths = json.loads(response_text)
    except json.JSONDecodeError:
        selected_paths = [response_text]

    matched_files = []
    for path in selected_paths:
        match = next((item for item in metadata if item["path"] == path), None)
        if match:
            matched_files.append(FileMetadata(
                path=match["path"],
                type=match["type"],
                geometry=match.get("geometry", ""),
                fields=match["fields"],
                features=match["features"],
                crs=match.get("crs", "Unknown"),
                description=match["description"]
            ))

    return FileSearchResult(files=matched_files)

