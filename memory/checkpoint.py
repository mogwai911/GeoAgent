# memory/checkpoint.py (LangGraph-compatible memory saver)

import os
import json
from langgraph.checkpoint.base import BaseCheckpointSaver

class MemorySaver(BaseCheckpointSaver):
    """
    Saves and loads agent state checkpoints as JSON files
    in a local directory (default: .checkpoints).
    """
    def __init__(self, path: str = ".checkpoints"):
        os.makedirs(path, exist_ok=True)
        self.path = path

    def get_path(self, name: str) -> str:
        return os.path.join(self.path, f"{name}.json")

    def put(self, config, state, name):
        with open(self.get_path(name), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def get(self, config, name):
        path = self.get_path(name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

