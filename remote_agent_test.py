from strands import Agent
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import sys
import os
import boto3
import yaml
import requests
import urllib.parse
import logging
import uuid
from typing import Any, Optional

agent_name = "ep_agent"
prompt = "Hello!"

def get_aws_region() -> str:
    return os.environ.get("AWS_REGION", "us-east-1")

def invoke_endpoint(
    agent_arn: str,
    payload,
    session_id: str,
    bearer_token: Optional[str],
    endpoint_name: str = "DEFAULT",
) -> Any:
    escaped_arn = urllib.parse.quote(agent_arn, safe="")
    url = f"https://bedrock-agentcore.{get_aws_region()}.amazonaws.com/runtimes/{escaped_arn}/invocations"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    }

    try:
        body = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        body = {"payload": payload}

    try:
        response = requests.post(
            url,
            params={"qualifier": endpoint_name},
            headers=headers,
            json=body,
            timeout=100,
            stream=True,
        )
        logger = logging.getLogger("bedrock_agentcore.stream")
        logger.setLevel(logging.INFO)

        last_data = False
        content = []  # Initialize content list

        for line in response.iter_lines(chunk_size=1):
            if line:
                line = line.decode("utf-8")
                print(line)
                if line.startswith("data: "):
                    last_data = True
                    line_content = line[6:].replace('"', "")
                    content.append(line_content)
                    print(line_content, end="")
                elif line:
                    if last_data:
                        line_content = line.replace('"', "")
                        content.append(line_content)
                        print("\n" + line_content, end="")
                    last_data = False

        print({"response": "\n".join(content)})

    except requests.exceptions.RequestException as e:
        print("Failed to invoke agent endpoint:", str(e))
        raise

try:
    # Load gateway configuration
    print("Loading gateway configuration...")
    with open('agent_config.json', 'r') as f:
        config = json.load(f)
    print("✓ Configuration loaded")
    
    # Check for AWS credentials
    print("Checking AWS credentials...")
    if not os.environ.get('AWS_ACCESS_KEY_ID') and not os.environ.get('AWS_PROFILE'):
        # Try to get session token if it's available in the environment
        session_token = os.environ.get('AWS_SESSION_TOKEN')
        if session_token:
            print("Using AWS Session Token from environment")
        else:
            print("⚠️ No AWS credentials found in environment")
            print("You may need to configure AWS credentials using AWS CLI or environment variables")

    # Get access token from Cognito
    print("Getting access token...")
    client = GatewayClient(region_name="us-east-1")
    access_token = client.get_access_token_for_cognito(config['cognito_info']['client_info'])
    print("✓ Access token obtained")

    with open(".bedrock_agentcore.yaml", 'r') as f:
        runtime_config = yaml.safe_load(f)

    # print(runtime_config)

    if agent_name not in runtime_config["agents"]:
        print(f"❌ Agent {agent_name} not found in config.")
        sys.exit(1)

    print(f"✓ Agent {agent_name} found in config.")

    agent_arn = runtime_config["agents"][agent_name]["bedrock_agentcore"]["agent_arn"]

    # Define a function to invoke the agent
    def invoke_agent(input_prompt):
        return invoke_endpoint(
            agent_arn=agent_arn,
            payload=json.dumps({"prompt": input_prompt, "actor_id": "DEFAULT"}),
            bearer_token=access_token,
            session_id=str(uuid.uuid4()),
        )
    
    # Initial greeting message
    print("\n" + "="*50)
    print("🤖 AI Agent Ready!")
    print("Ask questions about questions or answers")
    print("Type 'exit' or 'quit' to stop.")
    print("="*50 + "\n")
    
    # Interactive chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye! 👋")
                break
            
            if not user_input:
                continue
                
            print("Agent: ", end="", flush=True)
            invoke_agent(user_input)
            print()  # Add newline after response
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            # Print more detailed error information
            import traceback
            error_details = traceback.format_exc()
            print(f"Error details:\n{error_details}")
            print("Please try again or type 'exit' to quit.\n")

except FileNotFoundError:
    print("❌ agent_config.json not found")
    print("Please run create_gateway_with_targets.py first")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to initialize agent: {e}")
    print("Please check your configuration and try again")
    sys.exit(1)
