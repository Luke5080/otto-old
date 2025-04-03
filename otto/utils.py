import os
import mysql.connector
import pyfiglet
from colorama import Fore, Style

from otto.otto_logger.logger_config import logger

def check_default_credentials():
     auth_database_connection = mysql.connector.connect(
            user='root', password='root', host='localhost', port=3306, database='authentication_db')

     cursor = auth_database_connection.cursor()

     cursor.execute(
                "SELECT * from users;"
     )
     result = cursor.fetchall()
     for user in result:
         if user[0] and user[1] == "admin":
            logger.warn("Using default password for user 'admin'. Please change the password")

     auth_database_connection.close()
def check_api_keys():
    platforms_to_check = {
        "OPENAI_API_KEY": "OpenAi",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "LLAMA_API_KEY": "Llama",
        "ANTHROPIC_API_KEY": "Claude"
    }

    for platform in platforms_to_check.keys():
        if not os.environ.get(platform):
            logger.warn(f"API key not set for model provider {platforms_to_check[platform]}")


def create_shell_banner(model: str, controller: str, api_endpoints: bool,
                        dashboard: bool, verbosity_level: str):

    banner = f"""
    {Fore.CYAN}
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
