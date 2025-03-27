import os

from otto.otto_logger.logger_config import logger


def check_api_keys():
    platforms_to_check = {
        "OPENAI_API_KEY": "OpenAi",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "LLAMA_API_KEY": "Llama",
        "CLAUDE_API_KEY": "Claude"
    }

    for platform in platforms_to_check.keys():
        if not os.environ.get(platform):
            logger.warn(f"API key not set for model provider {platforms_to_check[platform]}")
