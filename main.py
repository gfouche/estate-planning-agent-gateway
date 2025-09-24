"""
Main agent entry point with M2M authentication to AgentCore Gateway
"""
import asyncio
import os
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.identity.auth import requires_access_token

# Import from flattened structure
from gateway_client import GatewayClient
from settings import Settings
from agent_factory import create_agent
from setup_identity import setup_m2m_credential_provider

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize components
settings = Settings()

# Set up identity provider for M2M auth
credential_provider = setup_m2m_credential_provider()
logging.info(f"Identity provider initialized: {settings.M2M_PROVIDER_NAME}")

agent = create_agent(model_id=settings.MODEL_ID, region_name=settings.REGION)
app = BedrockAgentCoreApp()
gateway_client = GatewayClient(
    gateway_url=settings.GATEWAY_URL,
    provider_name=settings.M2M_PROVIDER_NAME
)

@app.entrypoint
def invoke(payload):
    """Main agent entry point"""
    try:
        user_message = payload.get("prompt", "Hello")
        logging.info(f"Received payload: {payload}")

        # Route to appropriate handler
        if "questions" in user_message.lower():
            logging.info("Routing to handle_questions_request")
            result = asyncio.run(handle_questions_request(user_message))
            logging.info(f"handle_questions_request result: {result}")
            return result
        elif "gateway" in user_message.lower():
            logging.info("Routing to handle_gateway_request")
            result = asyncio.run(handle_gateway_request(user_message))
            logging.info(f"handle_gateway_request result: {result}")
            return result
        else:
            # Standard agent processing
            logging.info("Routing to standard agent processing")
            response = agent(user_message)
            logging.info(f"Agent response: {response}")
            return response

    except Exception as e:
        logging.error(f"Error during invoke: {str(e)}")
        return f"Error: {str(e)}"

async def handle_questions_request(message: str) -> str:
    """Handle questions-related requests via gateway"""
    try:
        result = await gateway_client.call_tool(
            "get_questions",
            {"docType": "Will"}
        )
        return f"Questions data: {result}"
    except Exception as e:
        return f"Questions service error: {str(e)}"

async def handle_gateway_request(message: str) -> str:
    """Handle general gateway requests"""
    try:
        # Use semantic search to find relevant tools
        tools = await gateway_client.search_tools(message)
        return f"Found {len(tools)} relevant tools: {tools}"
    except Exception as e:
        return f"Gateway error: {str(e)}"

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent")
    if agent:
        app.run()
        logging.info("Agent shutdown")
    else:
        logging.error("Cannot start application: Agent was not properly initialized")