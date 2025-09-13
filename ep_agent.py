from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import os

def create_agent():
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )
    agent = Agent(model=model)
    return agent

# Load the agent configuration file
config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
with open(config_path, "r") as f:
    config = json.load(f)

# Create the agent and gateway client
agent = create_agent()
app = BedrockAgentCoreApp()
gateway_client = GatewayClient(region_name="us-east-1")

@app.entrypoint
def invoke(payload):
    """Your AI agent function"""
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    session_id = payload.get("session_id")
    
    # Get auth token for API calls using the gateway client
    auth_token = None
    if "cognito_info" in config and "client_info" in config["cognito_info"]:
        try:
            auth_token = gateway_client.get_access_token_for_cognito(
                config["cognito_info"]["client_info"]
            )
        except Exception:
            pass
    
    # Process with the agent
    result = agent(user_message, session_id=session_id)
    
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
