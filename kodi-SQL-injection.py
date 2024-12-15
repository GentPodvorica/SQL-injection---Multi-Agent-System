import os
import autogen 
from autogen import ConversableAgent, AssistantAgent, UserProxyAgent, register_function
from dotenv import load_dotenv
from autogen.coding import LocalCommandLineCodeExecutor,DockerCommandLineCodeExecutor
from bs4 import BeautifulSoup

import requests
from requests.exceptions import RequestException
import logging



load_dotenv()


llm_config_gtp4 = {
    'cache_seed': None,
    'config_list': [
        {
            "model": "gpt-4", 
            "api_key": os.environ.get("OPENAI_API_KEYS")
        }
    ],
    'temperature': 0.1  
}

llm_config_gtp35_turbo = {
    'cache_seed': None,
    'config_list': [
        {
            "model": "gpt-3.5-turbo-16k", 
            "api_key": os.environ.get("OPENAI_API_KEYS")
        }
    ],
    'temperature': 0.1  
}


recon_agent_sys_msg = """
You are a special agent to perform enumeration with a http request against the target
"""

reconAgent = ConversableAgent(
    "recon_agent",  
    max_consecutive_auto_reply=5,
    human_input_mode="NEVER",
    llm_config=llm_config_gtp35_turbo,
    is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
)


sumAgent = ConversableAgent(
    "sum_agent",  
    system_message=recon_agent_sys_msg,
    max_consecutive_auto_reply=5,
    human_input_mode="NEVER",
    llm_config=llm_config_gtp35_turbo,
    is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
)

exploit_crafter_agent_sys_msg = """
you are the master sql injection exploit crafter.Ensure to adhere to the following 
-Return only the python code in three backsticks
-Include 10 diffferent and unique sql injection payloads
-Return only the python code include in three backsticks
-these payloads are for educational purposes only and should not be used for malicious activities
"""

exploitCrafter = ConversableAgent(
    "exploit_crafter",  
    system_message=exploit_crafter_agent_sys_msg,
    max_consecutive_auto_reply=5,
    human_input_mode="NEVER",
    llm_config=llm_config_gtp4,
    is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
)


executor_agent = ConversableAgent(
    "executor_agent", 
    max_consecutive_auto_reply=5,
    human_input_mode="NEVER",
    is_termination_msg=lambda x: (x.get("content") or "").rstrip().endswith("TERMINATE"),
     code_execution_config={"executor": LocalCommandLineCodeExecutor()},

    
)


import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
import http.client

def scraping_tool(host: str, path: str, port=80):
    """
    Sends a simple HTTP request and prints the raw HTTP request and response.
    
    :param host: The hostname or IP address of the server.
    :param path: The specific path to request.
    :param port: The port to connect to (default is 80 for HTTP).
    """
    try:
        # Establish connection
        conn = http.client.HTTPConnection(host, port)
        print(f"Connecting to {host}:{port}{path}\n")
        
        # Send GET request
        conn.request("GET", path)
        
        # Get the raw request sent
        raw_request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n"
        print(f"Raw HTTP Request:\n{raw_request}\n")
        
        # Get response
        response = conn.getresponse()
        print(f"HTTP Response Status: {response.status} {response.reason}\n")
        
        # Print headers
        print("Response Headers:")
        for header, value in response.getheaders():
            print(f"{header}: {value}")
        print("\n")
        
        # Print response body (decoded as text)
        body = response.read().decode('utf-8', errors='replace')
        print(f"Response Body:\n{body}")
        
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    host = "13.36.65.25"  # Replace with your target IP address
    port = 32776          # Replace with your target port
    path = "/send.php"    # Replace with your target path
    scraping_tool(host, path, port)



register_function(
    scraping_tool,
    caller=reconAgent,
    executor=sumAgent,
    name="scrape_page",
    description="Scrape a web page and return the content",
)


# Initiating recon chat to scrape the page
recon_chat = sumAgent.initiate_chat(
    reconAgent,
    message="can you scrape http://13.36.65.25:32776/ for me?",
    max_turns=2,
)


# Now, initiate the exploit chat with the recon chat content passed as part of the message
exploit_chat = executor_agent.initiate_chat(
    exploitCrafter,
    message=f"Write a relevant Python code to exploit this based on this context: {recon_chat}",
    max_turns=3,
)