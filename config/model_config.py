import os
import time
from typing import Dict, Any, Optional

# Global variable to store VLLM IP
VLLM_IP: Optional[str] = None

def get_vllm_ip() -> str:
    """
    Get the VLLM server IP address from either global variable or qwen_ip.txt file.
    Waits for the file to be available if necessary.
    
    Returns:
        str: The VLLM server IP address with port
    """
    global VLLM_IP
    
    if VLLM_IP:
        return VLLM_IP
        
    ip_file = os.path.expanduser("/home/kaiyuan/lu2025-17-15/Kaiyuan/qwen_ip.txt")
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

# Local model configuration (OpenAI API compatible format)
LLM_MODEL: Dict[str, Any] = {
    "base_url": f"{get_vllm_ip()}/v1",  # Local model service endpoint
    "api_key": "not-needed",            # Not needed for local deployment
    "model_name": "Qwen72B"     # Model name
}

def get_model_config() -> Dict[str, Any]:
    """
    Get the model configuration in OpenAI compatible format.
    
    Returns:
        Dict[str, Any]: Model configuration dictionary
    """
    # Update base_url with current VLLM IP in case it changed
    LLM_MODEL["base_url"] = f"{get_vllm_ip()}/v1"
    return LLM_MODEL 