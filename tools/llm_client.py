# tools/llm_client.py (LangGraph-compatible wrapper for local Qwen)

import os
import time
import requests
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import List

# === Get Local vLLM IP ===
VLLM_IP = None

def get_vllm_ip():
    global VLLM_IP
    if VLLM_IP:
        return VLLM_IP

    ip_file = os.path.expanduser("~/qwen_ip.txt")
    wait_time = 30

    while not os.path.exists(ip_file) and wait_time > 0:
        print("Waiting for qwen_ip.txt to be available...")
        time.sleep(3)
        wait_time -= 3

    if os.path.exists(ip_file):
        with open(ip_file, "r") as f:
            node_ip = f.read().strip()
            if not node_ip.startswith("http"):
                node_ip = f"http://{node_ip}:8000"
            VLLM_IP = node_ip
            return VLLM_IP
    else:
        raise RuntimeError("Failed to locate Qwen server IP.")

# === Convert LangChain Messages to OpenAI Format ===
def format_messages(messages: List) -> List[dict]:
    formatted = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            continue
        formatted.append({"role": role, "content": msg.content})
    return formatted

# === LangChain-compatible Qwen Wrapper ===
class QwenChat(BaseChatModel):
    model: str = "Qwen/Qwen2.5-14B-Instruct"
    temperature: float = 0.7
    
    def bind_tools(self, tool_classes):
        # 🛠Pseudo implementation, LangGraph needs it but we won't use tool calling
        return self

    def _call(self, messages: List, **kwargs) -> str:
        ip = get_vllm_ip()
        payload = {
            "model": self.model,
            "messages": format_messages(messages),
            "temperature": self.temperature
        }
        try:
            response = requests.post(f"{ip}/v1/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Qwen API Error] {e}"

    def _generate(self, messages: List, stop=None, run_manager=None, **kwargs) -> ChatResult:
        content = self._call(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "qwen-local"


