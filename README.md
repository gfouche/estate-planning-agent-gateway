# Estate Planning Agent Gateway

This project provides a gateway interface for the Estate Planning agent, connecting a strands agent to AWS Bedrock AgentCore.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Configure the agent by updating the `agent_config.json` file with your Cognito credentials.

## Usage

### Running the Agent Locally

To run the agent locally for testing:

```bash
python ep_agent.py
```

This will start a local server at http://localhost:8080.

### Testing with the Local Interface

In a separate terminal, use the testing interface to interact with the agent:

```bash
python testing_agent_local.py
```

### Connecting to AWS AgentCore Gateway

To connect to the AWS AgentCore Gateway, ensure your `agent_config.json` file has the correct Cognito information:

```json
{
  "cognito_info": {
    "client_info": {
      "client_id": "YOUR_CLIENT_ID",
      "client_secret": "YOUR_CLIENT_SECRET",
      "user_pool_id": "YOUR_USER_POOL_ID",
      "token_endpoint": "YOUR_TOKEN_ENDPOINT",
      "scope": "YOUR_SCOPE",
      "domain_prefix": "YOUR_DOMAIN_PREFIX"
    }
  }
}
```

Then deploy the agent using the included PowerShell script:

```powershell
.\deploy.ps1 -FunctionName <your-lambda-name>
```

This will create a deployment package and upload it to AWS Lambda.

### Remote Agent Testing

To test the agent deployed to AWS:

```bash
python remote_agent_test.py
```

## Environment Variables

- `LOCAL_TEST`: Set to "true" to run in local testing mode (default: "false")
- `AWS_REGION`: AWS region to use (default: "us-east-1")