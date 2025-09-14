#!/usr/bin/env python
"""
Agent interaction utilities for the Estate Planning Agent CLI interface.
"""

import requests
import json
from typing import Dict, Any, Optional
from utils.formatting import Colors


def invoke_agent(prompt: str, 
                session_id: Optional[str] = None, 
                endpoint: str = "http://localhost:8080/invocations") -> Dict[str, Any]:
    
    headers = {
        # "Authorization": f"Bearer {bearer_token}",    
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }

    payload = {
        "prompt": prompt
    }
    
    if session_id:
        payload["session_id"] = session_id

    try:
        body = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        body = {"payload": payload}
        
    print(f"\n{Colors.YELLOW}Sending request to: {endpoint}{Colors.END}")
    print(f"{Colors.YELLOW}Session ID: {session_id}{Colors.END}")
    print(f"{Colors.YELLOW}Payload: {json.dumps(payload, indent=2)}{Colors.END}")

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=100,
            stream=True,
        )
        
        # Parse and return the JSON response
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"\n{Colors.RED}Error connecting to agent: {str(e)}{Colors.END}")
        if hasattr(e, "response") and e.response:
            try:
                error_data = e.response.json()
                print(f"{Colors.RED}Error details: {json.dumps(error_data, indent=2)}{Colors.END}")
            except:
                print(f"{Colors.RED}Response content: {e.response.text}{Colors.END}")
        return {
            "result": "Error: Failed to connect to the agent. Is it running?", 
            "error": str(e)
        }