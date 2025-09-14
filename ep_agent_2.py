
import token
from strands import Agent
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

access_token = None
gateway_url = None

logging.info("Initializing Gateway Client")
gateway_client = GatewayClient(region_name="us-east-1")

config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
logging.info(f"Loading configuration from {config_path}")
try:
    with open(config_path, "r") as f:
        config = json.load(f)
    logging.info("Configuration loaded successfully")

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
                
        except Exception as e:
            logging.error(f"Error accessing gateway: {str(e)}", exc_info=True)

    else:
        logging.error("Missing required configuration: cognito_info or client_info not found in config")

except Exception as e:
    logging.error(f"Error loading configuration: {str(e)}")
    config = {"gateway_url": "", "cognito_info": {"client_info": {}}}

def create_agent(access_token: str, gateway_url: str) -> Agent:
 
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

app = BedrockAgentCoreApp()
agent = create_agent(access_token, gateway_url)

@app.entrypoint
def invoke(payload, context):

    """Process incoming requests using the MCP client"""
    user_message = payload["prompt"]
    session_id = context.session_id

    if not session_id:
        raise Exception("Session ID is required in the context")
    
    logging.info(f"Received request with session ID: {session_id}")

    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
