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
    headers = {"Authorization": f"Bearer {access_token}"}
    logging.info(f"Creating HTTP transport for URL: {mcp_url} with headers: Authorization: Bearer {access_token[:10]}...{access_token[-5:] if len(access_token) > 15 else ''}")
    return streamablehttp_client(mcp_url, headers=headers)

def get_full_tools_list(client):
    """Get all tools from the MCP client"""
    logging.info("Fetching tools from MCP gateway")
    more_tools = True
    tools = []
    pagination_token = None
    page_count = 0
    
    try:
        while more_tools:
            page_count += 1
            logging.info(f"Fetching tools page {page_count}")
            tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
            
            # Log the raw response for debugging
            logging.info(f"Raw tools response: {str(tmp_tools)[:500]}")
            
            # Check if the tmp_tools is None or empty
            if not tmp_tools:
                logging.warning("Received empty tools response")
                break
                
            tools.extend(tmp_tools)
            
            # Log details about each tool
            for i, tool in enumerate(tmp_tools):
                try:
                    tool_info = {
                        "tool_name": getattr(tool, "tool_name", "unknown"),
                        "tool_id": getattr(tool, "tool_id", "unknown"),
                        "description": getattr(tool, "description", "")[:100]
                    }
                    logging.info(f"Tool {i+1}: {json.dumps(tool_info)}")
                except Exception as tool_err:
                    logging.error(f"Error logging tool details: {str(tool_err)}")
            
            if tmp_tools.pagination_token is None:
                more_tools = False
                logging.info("No more tool pages")
            else:
                more_tools = True
                pagination_token = tmp_tools.pagination_token
                logging.info(f"More tools available, pagination token: {pagination_token}")
    
    except Exception as e:
        logging.error(f"Error fetching tools: {str(e)}", exc_info=True)
        # Try to get more details about the error
        if hasattr(e, "response"):
            try:
                logging.error(f"Tools API Response status: {e.response.status_code}")
                logging.error(f"Tools API Response content: {e.response.text}")
            except:
                pass
    
    tool_names = [getattr(tool, "tool_name", "unknown") for tool in tools]
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
            # Log client info (with sensitive data masked)
            client_info = config["cognito_info"]["client_info"].copy()
            if "client_secret" in client_info:
                secret = client_info["client_secret"]
                client_info["client_secret"] = f"{secret[:5]}...{secret[-5:]}" if len(secret) > 10 else "***masked***"
            logging.info(f"Client info parameters: {json.dumps(client_info)}")
            
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
                try:
                    tools = get_full_tools_list(mcp_client)
                    agent = create_agent(tools=tools)
                    
                    # Process with the agent
                    logging.info("Processing message with agent using gateway tools")
                    logging.info(f"Request parameters - Message: '{user_message[:50]}...' Session ID: {session_id}")
                    result = agent(user_message, session_id=session_id)
                    logging.info(f"Raw response from agent: {str(result)[:500]}")
                    logging.info("Request processed successfully")
                    return {"result": result.message}
                except Exception as inner_e:
                    logging.error(f"Error during gateway interaction: {str(inner_e)}", exc_info=True)
                    # Try to get more details about the error
                    if hasattr(inner_e, "response"):
                        try:
                            logging.error(f"Response status: {inner_e.response.status_code}")
                            logging.error(f"Response content: {inner_e.response.text}")
                        except:
                            pass
                    raise inner_e
                
        except Exception as e:
            logging.error(f"Error accessing gateway: {str(e)}", exc_info=True)
            # Include the exception type in the error message
            error_type = type(e).__name__
            return {"result": f"Error accessing gateway: {error_type} - {str(e)}"}

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
