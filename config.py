"""
Configuration settings for the application.
"""

# Model configurations
QWEN_MAX_CONFIG = {
    "model": "qwen-max",
    "api_key": "",  # Add your API key here
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model_info": {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "UNKNOWN",
        "structured_output": True,
    },
    "temperature": 0.1,
    "max_tokens": 8192
}

DEEPSEEK_CONFIG = {
    "model": "deepseek-chat",
    "api_key": "",  # Add your API key here
    "base_url": "https://api.deepseek.com/v1",
    "model_info": {
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "family": "UNKNOWN",
        "structured_output": False,
    },
    "temperature": 0.3,
    "max_tokens": 8192
} 