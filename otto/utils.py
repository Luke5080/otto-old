import os

import pyfiglet
from colorama import Fore, Style

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


def create_shell_banner(model: str, controller: str, api_endpoints: bool,
                        dashboard: bool, verbosity_level: str):

    banner = f"""
    {pyfiglet.figlet_format('OTTO', font='dos_rebel')}
    
    {Style.BRIGHT}
    Author: Luke Marshall
    
    Configured model: {model}
    Configured Controller: {controller}
    
    API Endpoint Status: {'ON' if api_endpoints else 'OFF'}
    Dashboard Status: {'ON' if dashboard else 'OFF'}
    
    Agent Output Verbosity Level: {verbosity_level}
    
    {Fore.RESET}
    """

    return banner
