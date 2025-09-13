from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import os
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_streamable_http_transport(mcp_url, access_token):
    """Create a streamable HTTP transport with authorization header"""
    return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})

def get_full_tools_list(client):
    """Get all tools from the MCP client"""
    logging.info("Fetching tools from MCP gateway")
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    
    tool_names = [tool.tool_name for tool in tools]
    logging.info(f"Found {len(tools)} tools: {', '.join(tool_names) if tool_names else 'none'}")
    return tools

def create_agent(tools=None):
    """Create and configure the strands agent"""
    logging.info("Creating BedrockModel with Claude Sonnet")
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )
    tool_count = len(tools) if tools else 0
    logging.info(f"Initializing Agent with {tool_count} tools")
    agent = Agent(model=model, tools=tools)
    return agent

# Load the agent configuration file
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
logging.info(f"Loading configuration from {config_path}")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
    logging.info("Configuration loaded successfully")
except Exception as e:
    logging.error(f"Error loading configuration: {str(e)}")
    config = {"gateway_url": "", "cognito_info": {"client_info": {}}}

# Set up the agent core app
logging.info("Initializing BedrockAgentCoreApp")
app = BedrockAgentCoreApp()
logging.info("Initializing Gateway Client")
gateway_client = GatewayClient(region_name="us-east-1")

@app.entrypoint
def invoke(payload):
    """Process incoming requests using the MCP client"""
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    session_id = payload.get("session_id")
    
    logging.info(f"Received request with session ID: {session_id}")
    
    # Get auth token for API calls using the gateway client
    access_token = None
    gateway_url = None
    
    if "cognito_info" in config and "client_info" in config["cognito_info"]:
        try:
            logging.info("Getting access token from Cognito")
            access_token = gateway_client.get_access_token_for_cognito(
                config["cognito_info"]["client_info"]
            )
            logging.info("Access token obtained successfully")
            
            # Get gateway URL from configuration
            gateway_url = config.get("gateway_url", "https://your-gateway-url.amazonaws.com")
            logging.info(f"Using gateway URL: {gateway_url}")
            
            # Create MCP client with streamable HTTP transport
            logging.info("Creating MCP client with streamable HTTP transport")
            mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_url, access_token))
            
            # Get tools and create agent with them
            with mcp_client:
                tools = get_full_tools_list(mcp_client)
                agent = create_agent(tools=tools)
                
                # Process with the agent
                logging.info("Processing message with agent using gateway tools")
                result = agent(user_message, session_id=session_id)
                logging.info("Request processed successfully")
                return {"result": result.message}
                
        except Exception as e:
            logging.error(f"Error accessing gateway: {str(e)}")
            return {"result": f"Error accessing gateway: {str(e)}"}
    
    # Fallback to regular agent if gateway is not configured
    logging.info("Using fallback agent without gateway tools")
    agent = create_agent()
    result = agent(user_message, session_id=session_id)
    logging.info("Request processed with fallback agent")
    return {"result": result.message}

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
