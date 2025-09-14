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
    """
    Send a request to the locally running agent and return the response.
    
    Args:
        prompt: The user message to send to the agent
        session_id: Optional session ID for continuing a conversation
        endpoint: The URL of the local agent endpoint
        
    Returns:
        The parsed JSON response from the agent
    """
    # Prepare the request payload
    payload = {"prompt": prompt}
    if session_id:
        payload["session_id"] = session_id
        
    try:
        # Send the request to the local agent
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
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