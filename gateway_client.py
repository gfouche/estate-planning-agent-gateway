"""
Gateway client with M2M authentication for DIY Will Agent using actual gateway tool schema
"""
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient
from bedrock_agentcore.identity.auth import requires_access_token

class WillGatewayClient:
    def __init__(self, gateway_url: str, provider_name: str):
        self.gateway_url = gateway_url
        self.provider_name = provider_name

    @requires_access_token(
        provider_name="estate-planning-m2m-provider",
        scopes=[],
        auth_flow='M2M',
        force_authentication=False
    )
    async def get_mcp_client(self, *, access_token: str) -> MCPClient:
        """Get MCP client with current access token"""
        def create_transport():
            return streamablehttp_client(
                url=self.gateway_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
        return MCPClient(create_transport)

        """List all available will creation tools"""
        mcp_client = await self.get_mcp_client()

        with mcp_client:
            tools = mcp_client.list_tools_sync()
            return [
                {
                    "name": tool.tool_name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                for tool in tools
            ]