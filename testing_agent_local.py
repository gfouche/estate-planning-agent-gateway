#!/usr/bin/env python
"""
Local Agent Test - Interactive Testing for Estate Planning Agent
This script provides an interactive command-line interface for testing
the locally running estate planning agent.
"""

import requests
import json
import uuid
import os
import argparse
import sys
from typing import Dict, Any, Optional

# ANSI color codes for terminal output formatting
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

def print_header():
    """Print a welcome header for the test interface."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}=" * 70)
    print("🔍 ESTATE PLANNING AGENT - LOCAL TESTING INTERFACE")
    print("=" * 70)
    print(f"""
This interface lets you interactively test your local estate planning agent.
- Type your questions or responses and press Enter
- Type {Colors.YELLOW}'clear'{Colors.BLUE} to start a new conversation
- Type {Colors.YELLOW}'state'{Colors.BLUE} to see the current agent state
- Type {Colors.YELLOW}'exit'{Colors.BLUE} or {Colors.YELLOW}'quit'{Colors.BLUE} to end the session
""")
    print(f"=" * 70 + Colors.END)

def invoke_agent(prompt: str, session_id: Optional[str] = None, endpoint: str = "http://localhost:8080/invocations") -> Dict[str, Any]:
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
        return {"result": "Error: Failed to connect to the agent. Is it running?", "error": str(e)}

def display_response(response: Dict[str, Any]):
    """
    Display the agent's response with formatting.
    
    Args:
        response: The parsed JSON response from the agent
    """
    # Display the main response message
    if "result" in response:
        print(f"\n{Colors.GREEN}🤖 Agent: {Colors.END}{response['result']}")
    
    # Display metadata if available (but hide error details)
    metadata = {k: v for k, v in response.items() if k not in ["result", "error_details"] and not k.startswith("_")}
    if metadata and metadata != {"error": None}:
        print(f"\n{Colors.YELLOW}Metadata:{Colors.END}")
        for key, value in metadata.items():
            if key != "error" or value is not None:
                print(f"  {Colors.YELLOW}{key}:{Colors.END} {value}")

def main():
    """Main function to run the interactive testing interface."""
    parser = argparse.ArgumentParser(description="Test the estate planning agent locally")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8080/invocations",
                        help="URL of the local agent endpoint (default: http://localhost:8080/invocations)")
    parser.add_argument("--session", type=str, default=None,
                        help="Session ID to continue an existing conversation (default: generate new ID)")
    args = parser.parse_args()
    
    print_header()
    
    # Generate a unique session ID for this conversation or use the provided one
    session_id = args.session or str(uuid.uuid4())
    conversation_history = []
    
    print(f"{Colors.BOLD}Using session ID: {session_id}{Colors.END}\n")
    
    try:
        while True:
            # Get user input
            user_input = input(f"{Colors.BOLD}You: {Colors.END}")
            
            # Handle special commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(f"\n{Colors.BLUE}👋 Goodbye! Thanks for testing the Estate Planning Agent.{Colors.END}\n")
                break
                
            if user_input.lower() == "clear":
                session_id = str(uuid.uuid4())
                conversation_history = []
                print(f"\n{Colors.BLUE}🔄 Starting new conversation with session ID: {session_id}{Colors.END}\n")
                continue
                
            if user_input.lower() == "state":
                print(f"\n{Colors.YELLOW}Conversation History:{Colors.END}")
                for i, (role, text) in enumerate(conversation_history):
                    prefix = "🤖 Agent" if role == "agent" else "👤 You"
                    print(f"{i+1}. {Colors.BOLD}{prefix}:{Colors.END} {text}")
                continue
                
            # If no special command, send the input to the agent
            if user_input.strip():
                # Record the user message
                conversation_history.append(("user", user_input))
                
                # Send the message to the agent
                response = invoke_agent(user_input, session_id, args.endpoint)
                
                # Display the response
                display_response(response)
                
                # Record the agent response
                if "result" in response:
                    conversation_history.append(("agent", response["result"]))
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BLUE}👋 Session terminated. Thanks for testing the Estate Planning Agent.{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {str(e)}{Colors.END}")
        import traceback
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.END}")

if __name__ == "__main__":
    main()
