# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Estate Planning Agent Gateway that connects a strands agent to AWS Bedrock AgentCore. The agent uses MCP (Model Context Protocol) to communicate with AWS services and provides estate planning functionality through a Bedrock-based Claude Sonnet model.

## Key Commands

### Development & Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run agent locally (starts server on http://localhost:8080)
python ep_agent.py

# Test locally running agent (interactive CLI)
python testing/testing_agent_local.py

# Test remote deployed agent
python testing/remote_agent_test.py
```

### Docker Operations

```bash
# Build Docker image
docker build -t ep-agent .

# Run container locally
docker run -p 8080:8080 -p 8000:8000 ep-agent
```

### AWS Deployment

The project uses AWS Bedrock AgentCore for deployment. Configuration is managed through `.bedrock_agentcore.yaml` and `agent_config.json`.

## Architecture

### Core Components

1. **ep_agent.py**: Main agent implementation
   - Creates strands Agent with BedrockModel (Claude Sonnet)
   - Integrates MCP client for tool access via gateway
   - Handles Cognito authentication for AWS gateway access
   - Entry point for both local testing and AWS Lambda deployment

2. **Gateway Integration**:
   - Uses `bedrock-agentcore` and `bedrock-agentcore-starter-toolkit` for AWS integration
   - Authenticates via Cognito OAuth2 flow
   - Connects to MCP gateway endpoint for tool access

3. **Testing Framework** (testing/ directory):
   - `testing_agent_local.py`: Interactive CLI for local agent testing
   - `remote_agent_test.py`: Tests deployed AWS agent
   - `utils/`: Helper modules for formatting and agent invocation

### Configuration Files

- **agent_config.json**: Contains gateway URL and Cognito credentials
- **.bedrock_agentcore.yaml**: AWS deployment configuration including:
  - AWS account/region settings
  - ECR repository details
  - IAM execution roles
  - Cognito authorizer configuration

### Authentication Flow

1. Agent loads Cognito client credentials from `agent_config.json`
2. Requests access token from Cognito token endpoint
3. Uses bearer token to authenticate with MCP gateway
4. Gateway validates JWT against configured Cognito user pool

## Environment Variables

- `LOCAL_TEST`: Set to "true" for local testing mode (default: "false")
- `AWS_REGION`: AWS region (default: "us-east-1")
- `DOCKER_CONTAINER`: Automatically set when running in Docker

## Important Notes

- The agent uses Claude Sonnet model: `global.anthropic.claude-sonnet-4-20250514-v1:0`
- MCP tools are dynamically loaded from the gateway at runtime
- Agent requires valid Cognito credentials in `agent_config.json` to function
- Docker image uses Python 3.13 with UV package manager for fast dependency installation