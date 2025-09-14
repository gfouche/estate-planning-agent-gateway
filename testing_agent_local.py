#!/usr/bin/env python
"""
Local Agent Test - Interactive Testing for Estate Planning Agent
This script provides an interactive command-line interface for testing
the locally running estate planning agent.
"""

import uuid
import os
import argparse
import sys
import traceback
from typing import List, Tuple

# Import from our utility modules
from utils.formatting import Colors, print_header, display_response, display_conversation_history
from utils.agent import invoke_agent

def run_agent_loop(session_id: str, endpoint: str) -> None:
    """
    Run the main agent interaction loop.
    
    Args:
        session_id: The session ID to use for this conversation
        endpoint: The endpoint URL for the agent
    """
    conversation_history: List[Tuple[str, str]] = []
    
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
                display_conversation_history(conversation_history)
                continue
                
            # If no special command, send the input to the agent
            if user_input.strip():
                # Record the user message
                conversation_history.append(("user", user_input))
                
                # Send the message to the agent
                response = invoke_agent(user_input, session_id, endpoint)
                
                # Display the response
                display_response(response)
                
                # Record the agent response
                if "result" in response:
                    conversation_history.append(("agent", response["result"]))
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BLUE}👋 Session terminated. Thanks for testing the Estate Planning Agent.{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {str(e)}{Colors.END}")
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.END}")



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
    
    print(f"{Colors.BOLD}Using session ID: {session_id}{Colors.END}\n")
    
    # Start the agent interaction loop
    run_agent_loop(session_id, args.endpoint)

if __name__ == "__main__":
    main()
