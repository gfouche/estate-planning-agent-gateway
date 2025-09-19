#!/usr/bin/env python
"""
Remote Agent Test - Interactive Testing for Estate Planning Agent
This script provides an interactive command-line interface for testing
the remotely deployed estate planning agent in AWS Bedrock.
"""

import uuid
import os
import argparse
import sys
import traceback
from typing import List, Tuple

# Import from our utility modules
from utils.formatting import Colors, print_header, display_response, display_conversation_history
from utils.agent import invoke_agent, setup_remote_agent

def run_agent_loop(initial_session_id: str, agent_name: str) -> None:
    """
    Run the main agent interaction loop.
    
    Args:
        initial_session_id: The initial session ID to use for this conversation
        agent_name: The name of the agent in the configuration
    """
    conversation_history: List[Tuple[str, str]] = []
    
    # Set up the remote agent
    print(f"\n{Colors.BLUE}🔄 Setting up remote agent '{agent_name}'...{Colors.END}")
    setup_result = setup_remote_agent(agent_name)
    
    if setup_result.get("error"):
        print(f"\n{Colors.RED}❌ Error setting up remote agent: {setup_result['error']}{Colors.END}")
        return
        
    bearer_token = setup_result.get("bearer_token")
    agent_arn = setup_result.get("agent_arn")
    
    # Use the provided session ID or generate a new one if not provided
    session_id = initial_session_id if initial_session_id else str(uuid.uuid4())
    
    print(f"\n{Colors.GREEN}✓ Remote agent setup complete{Colors.END}")
    print(f"{Colors.BLUE}Agent ARN: {agent_arn}{Colors.END}")
    print(f"{Colors.BLUE}Using session ID: {session_id}{Colors.END}")
    
    try:
        while True:
            # Get user input
            user_input = input(f"{Colors.BOLD}You: {Colors.END}")
            
            # Handle special commands
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(f"\n{Colors.BLUE}👋 Goodbye! Thanks for testing the Estate Planning Agent.{Colors.END}\n")
                break
                
            if user_input.lower() == "clear":
                # Generate a new session ID for a fresh conversation
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
                
                # Use the same session ID for all interactions in the conversation
                # This allows the agent to maintain context across interactions
                print(f"\n{Colors.BLUE}Using session ID: {session_id}{Colors.END}")
                
                # Send the message to the agent
                print(f"{Colors.YELLOW}Sending message to remote agent...{Colors.END}")
                response = invoke_agent(
                    prompt=user_input, 
                    session_id=session_id, 
                    is_remote=True,
                    agent_arn=agent_arn,
                    bearer_token=bearer_token
                )
                
                # Add debugging info
                if "result" in response:
                    print(f"\n{Colors.BLUE}DEBUG: Response received with {len(response['result'])} characters{Colors.END}")
                else:
                    print(f"\n{Colors.RED}DEBUG: No 'result' field in response{Colors.END}")
                    print(f"{Colors.RED}Response keys: {list(response.keys())}{Colors.END}")
                
                # Display the response
                display_response(response)
                
                # Record the agent response
                if "result" in response:
                    # Store the message in conversation history
                    conversation_history.append(("agent", response["result"]))
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.BLUE}👋 Session terminated. Thanks for testing the Estate Planning Agent.{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}An error occurred: {str(e)}{Colors.END}")
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.END}")


def main():
    """Main function to run the interactive testing interface."""
    parser = argparse.ArgumentParser(description="Test the estate planning agent remotely")
    parser.add_argument("--agent", type=str, default="ep_agent",
                        help="Name of the agent to use (default: ep_agent)")
    parser.add_argument("--session", type=str, default=None,
                        help="Session ID to continue an existing conversation (default: generate new ID)")
    args = parser.parse_args()
    
    # Custom header with REMOTE instead of LOCAL
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print("🔍 ESTATE PLANNING AGENT - REMOTE TESTING INTERFACE")
    print("=" * 70)
    print(f"""
This interface lets you interactively test your remote estate planning agent.

{Colors.BOLD}Available Commands:{Colors.END}{Colors.BLUE}
- Type your questions or responses and press Enter
- Type {Colors.YELLOW}'clear'{Colors.BLUE} to start a new conversation
- Type {Colors.YELLOW}'state'{Colors.BLUE} to see the conversation history
- Type {Colors.YELLOW}'exit'{Colors.BLUE} or {Colors.YELLOW}'quit'{Colors.BLUE} to end the session
""")
    
    # Generate a unique session ID for this conversation or use the provided one
    session_id = args.session or str(uuid.uuid4())
    
    print(f"{Colors.BOLD}Using session ID: {session_id}{Colors.END}\n")
    
    # Start the agent interaction loop
    run_agent_loop(session_id, args.agent)

if __name__ == "__main__":
    main()