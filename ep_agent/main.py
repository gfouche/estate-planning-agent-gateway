"""
Main agent entry point with M2M authentication to AgentCore Gateway
"""
import asyncio
import os
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.identity.auth import requires_access_token

from ep_agent.tools.gateway_client import GatewayClient
from ep_agent.config.settings import Settings

# Initialize components
settings = Settings()
agent = Agent()
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
        
        # Route to appropriate handler
        if "weather" in user_message.lower():
            result = asyncio.run(handle_weather_request(user_message))
            return result
        elif "gateway" in user_message.lower():
            result = asyncio.run(handle_gateway_request(user_message))
            return result
        else:
            # Standard agent processing
            response = agent(user_message)
            return str(response)
            
    except Exception as e:
        return f"Error: {str(e)}"

async def handle_weather_request(message: str) -> str:
    """Handle weather-related requests via gateway"""
    try:
        result = await gateway_client.call_tool(
            "get_current_weather",
            {"city": "San Francisco", "country": "US"}
        )
        return f"Weather data: {result}"
    except Exception as e:
        return f"Weather service error: {str(e)}"

async def handle_gateway_request(message: str) -> str:
    """Handle general gateway requests"""
    try:
        # Use semantic search to find relevant tools
        tools = await gateway_client.search_tools(message)
        return f"Found {len(tools)} relevant tools: {tools}"
    except Exception as e:
        return f"Gateway error: {str(e)}"

if __name__ == "__main__":
    app.run()