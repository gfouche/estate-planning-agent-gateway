#!/usr/bin/env python
"""
Agent interaction utilities for the Estate Planning Agent CLI interface.
"""

import requests
import json
import urllib.parse
import os
import boto3
import yaml
from typing import Dict, Any, Optional, Union
from utils.formatting import Colors


def invoke_agent(prompt: str, 
                session_id: Optional[str] = None, 
                endpoint: str = "http://localhost:8080/invocations",
                is_remote: bool = False,
                agent_arn: Optional[str] = None,
                bearer_token: Optional[str] = None) -> Dict[str, Any]:
    
    if is_remote and (not agent_arn or not bearer_token):
        return {
            "result": "Error: Remote agent invocation requires agent_arn and bearer_token", 
            "error": "Missing required parameters for remote agent invocation"
        }

    headers = {
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }
    
    if is_remote and bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    # Different payload format for local vs remote
    if is_remote:
        payload = {
            "prompt": prompt,
            "actor_id": "DEFAULT"
        }
    else:
        payload = {
            "prompt": prompt
        }
    
    
    if session_id:
        payload["session_id"] = session_id

    try:
        body = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        body = {"payload": payload}
        
    print(f"\n{Colors.YELLOW}Sending request to: {endpoint if not is_remote else 'Remote Agent'}{Colors.END}")
    print(f"{Colors.YELLOW}Session ID: {session_id}{Colors.END}")
    print(f"{Colors.YELLOW}Payload: {json.dumps(payload, indent=2)}{Colors.END}")

    try:
        if is_remote:
            # Remote agent invocation
            region = os.environ.get("AWS_REGION", "us-east-1")
            escaped_arn = urllib.parse.quote(agent_arn, safe="")
            url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_arn}/invocations"
            
            print(f"{Colors.BLUE}Invoking remote agent at: {url}{Colors.END}")
            print(f"{Colors.BLUE}Request payload: {json.dumps(body)}{Colors.END}")
            
            response = requests.post(
                url,
                params={"qualifier": "DEFAULT"},
                headers=headers,
                json=body,
                timeout=120,  # Increased timeout
                stream=True,
            )
            
            # Process response from remote agent
            print(f"{Colors.BLUE}Receiving response from remote agent...{Colors.END}")
            
            try:
                # First, try to parse the entire response as a JSON object
                # (This is the format we're seeing in the debug output)
                response_text = ""
                line_count = 0
                json_response = None
                
                for line in response.iter_lines(chunk_size=1):
                    line_count += 1
                    if line:
                        decoded_line = line.decode("utf-8")
                        print(f"{Colors.YELLOW}DEBUG RAW[{line_count}]: {decoded_line}{Colors.END}")
                        response_text += decoded_line
                
                if response_text:
                    try:
                        json_response = json.loads(response_text)
                        print(f"{Colors.GREEN}Successfully parsed JSON response{Colors.END}")
                        
                        # Extract the message from the JSON response
                        if "message" in json_response:
                            message = json_response["message"]
                            print(f"{Colors.BLUE}Response received ({len(message)} characters from JSON){Colors.END}")
                            
                            # Return both the extracted message and the full JSON response
                            return {
                                "result": message, 
                                "raw_response": json_response,
                                "status": json_response.get("status", "unknown"),
                                "tools_used": json_response.get("tools_used", []),
                                "action_required": json_response.get("action_required", False),
                                "metadata": json_response.get("metadata", {})
                            }
                    except json.JSONDecodeError as e:
                        print(f"{Colors.RED}Failed to parse JSON response: {str(e)}{Colors.END}")
                        # Fall back to returning the raw text
                        return {"result": response_text}
                else:
                    print(f"{Colors.RED}No response text received{Colors.END}")
                    return {"result": "No response received from remote agent."}
                        
            except Exception as e:
                print(f"{Colors.RED}Error processing response: {str(e)}{Colors.END}")
                return {"result": f"Error processing agent response: {str(e)}"}
            
        else:
            # Local agent invocation
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


def get_agent_config() -> Dict[str, Any]:
    """
    Load the agent configuration from the config file.
    
    Returns:
        Dictionary containing the agent configuration.
    """
    try:
        with open('agent_config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"{Colors.RED}Error: agent_config.json not found.{Colors.END}")
        print(f"{Colors.RED}Please run create_gateway_with_targets.py first{Colors.END}")
        return {}


def get_agent_arn(agent_name: str) -> Optional[str]:
    """
    Get the ARN for the specified agent from the bedrock_agentcore config file.
    
    Args:
        agent_name: Name of the agent to lookup
        
    Returns:
        ARN string or None if not found
    """
    try:
        with open(".bedrock_agentcore.yaml", 'r') as f:
            runtime_config = yaml.safe_load(f)
            
        if agent_name not in runtime_config.get("agents", {}):
            print(f"{Colors.RED}Agent {agent_name} not found in config.{Colors.END}")
            return None
            
        return runtime_config["agents"][agent_name]["bedrock_agentcore"]["agent_arn"]
    except FileNotFoundError:
        print(f"{Colors.RED}Error: .bedrock_agentcore.yaml not found.{Colors.END}")
        return None


def setup_remote_agent(agent_name: str = "ep_agent") -> Dict[str, Any]:
    """
    Set up the remote agent with authentication.
    
    Args:
        agent_name: Name of the agent to set up
        
    Returns:
        Dictionary containing bearer_token, agent_arn and any error information
    """
    from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
    
    result = {
        "bearer_token": None,
        "agent_arn": None,
        "error": None
    }
    
    try:
        # Load agent configuration
        config = get_agent_config()
        if not config:
            result["error"] = "Failed to load agent configuration"
            return result
            
        # Get the agent ARN
        agent_arn = get_agent_arn(agent_name)
        if not agent_arn:
            result["error"] = f"Failed to find ARN for agent {agent_name}"
            return result
        
        result["agent_arn"] = agent_arn
            
        # Get authentication token
        client = GatewayClient(region_name="us-east-1")
        access_token = client.get_access_token_for_cognito(config['cognito_info']['client_info'])
        
        if not access_token:
            result["error"] = "Failed to obtain authentication token"
            return result
            
        result["bearer_token"] = access_token
        
    except Exception as e:
        result["error"] = str(e)
        
    return result