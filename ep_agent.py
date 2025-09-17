
from strands import Agent
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_configuration(config_path):
    """
    Load and validate configuration from the specified JSON file path
    
    Args:
        config_path (str): Path to the configuration JSON file
        
    Returns:
        dict: Configuration dictionary with default values if loading fails
    """
    logging.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logging.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        return {"gateway_url": "", "cognito_info": {"client_info": {}}}

def get_access_token(gateway_client, client_info):
    """
    Get access token from Cognito using the provided client info
    
    Args:
        gateway_client: Initialized GatewayClient instance
        client_info (dict): Cognito client information
        
    Returns:
        tuple: (access_token, None) if successful, (None, error_message) if failed
    """
    try:
        # Log client info (with sensitive data masked)
        safe_client_info = client_info.copy()
        if "client_secret" in safe_client_info:
            secret = safe_client_info["client_secret"]
            safe_client_info["client_secret"] = f"{secret[:5]}...{secret[-5:]}" if len(secret) > 10 else "***masked***"
        logging.info(f"Client info parameters: {json.dumps(safe_client_info)}")
        
        logging.info("Getting access token from Cognito")
        access_token = gateway_client.get_access_token_for_cognito(client_info)
        logging.info("Access token obtained successfully")
        return access_token, None
    except Exception as e:
        error_msg = f"Error accessing gateway: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return None, error_msg

def create_agent(config_path=None) -> Agent:
    """
    Create and initialize an Agent with Bedrock model and MCP client
    
    Args:
        config_path (str, optional): Path to the configuration JSON file. 
                                    If None, uses default path.
    
    Returns:
        Agent: Initialized Agent instance with model and tools
    """
    # Initialize Gateway Client
    logging.info("Initializing Gateway Client")
    gateway_client = GatewayClient(region_name="us-east-1")
    
    # Load configuration
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    
    config = load_configuration(config_path)
    access_token = None
    gateway_url = None
    
    # Get access token and gateway URL
    if "cognito_info" in config and "client_info" in config["cognito_info"]:
        access_token, error = get_access_token(
            gateway_client, 
            config["cognito_info"]["client_info"]
        )
        
        if access_token:
            # Get gateway URL from configuration
            gateway_url = config.get("gateway_url", "https://your-gateway-url.amazonaws.com")
            logging.info(f"Using gateway URL: {gateway_url}")
    else:
        logging.error("Missing required configuration: cognito_info or client_info not found in config")
        return None
    
    if not access_token or not gateway_url:
        logging.error("Failed to initialize agent: Missing access token or gateway URL")
        return None
 
    logging.info("Creating BedrockModel with Claude Sonnet us-east-1")
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )

    client = MCPClient(lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"}
    ))

    client.start()    
    logging.info("MCP Client created")

    tools = client.list_tools_sync()
    logging.info(f"Retrieved {len(tools)} tools from MCP gateway")
    
    return Agent(model=model, tools=tools)

def get_system_prompt():
    return """
You are an expert estate planning assistant. Your goal is to help users create and manage their estate plans, including wills, trusts, powers of attorney, and healthcare directives. You should provide clear, concise, and accurate information based on the user's needs and preferences.

"""  

app = BedrockAgentCoreApp()
agent = create_agent()

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    error_message: Optional[str] = None

class AgentResponse(BaseModel):
    status: str = Field(description="success, error, or partial")
    message: str = Field(description="Human-readable response")
    tools_used: List[ToolResult] = Field(default_factory=list)
    action_required: bool = Field(default=False, description="Whether user action is needed")
    metadata: dict = Field(default_factory=dict, description="Additional context")

@app.entrypoint
def invoke(payload, context):

    user_message = payload["prompt"]
    session_id = context.session_id

    if not session_id:
        raise Exception("Session ID is required in the context")
    
    logging.info(f"Received request with session ID: {session_id}")

    response = agent(user_message)
    structured_result = agent.structured_output(
        AgentResponse,
        "Format the response as JSON"
    )

    structured_result.message = str(response.message["content"][0]["text"])

    return structured_result

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
