"""
Gateway client with M2M authentication using AgentCore Identity caching
"""
import json
import requests
from typing import Dict, Any, List
from bedrock_agentcore.identity.auth import requires_access_token

class GatewayClient:
    def __init__(self, gateway_url: str, provider_name: str):
        self.gateway_url = gateway_url
        self.provider_name = provider_name
    
    @requires_access_token(
        provider_name="gateway-m2m-provider",  # Will be parameterized
        scopes=[],
        auth_flow='M2M',
        force_authentication=False  # Enable AgentCore caching
    )
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], *, access_token: str) -> Dict:
        """
        Call a specific tool via AgentCore Gateway
        AgentCore Identity automatically handles token caching and refresh
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(self.gateway_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    @requires_access_token(
        provider_name="gateway-m2m-provider",
        scopes=[],
        auth_flow='M2M',
        force_authentication=False
    )
    async def search_tools(self, query: str, *, access_token: str) -> List[Dict]:
        """
        Search for relevant tools using gateway's semantic search
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "x_amz_bedrock_agentcore_search",
                "arguments": {"query": query}
            }
        }
        
        response = requests.post(self.gateway_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "result" in result and "content" in result["result"]:
            return json.loads(result["result"]["content"][0]["text"])
        return []
    
    @requires_access_token(
        provider_name="gateway-m2m-provider",
        scopes=[],
        auth_flow='M2M',
        force_authentication=False
    )
    async def list_available_tools(self, *, access_token: str) -> List[Dict]:
        """
        List all available tools from the gateway
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        response = requests.post(self.gateway_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()