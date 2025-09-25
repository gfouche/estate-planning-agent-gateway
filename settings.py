"""
Configuration management for Estate Planning AgentCore application
"""
import os
from typing import Optional

class Settings:
    def __init__(self):
        # AgentCore Configuration
        self.REGION = os.getenv("AWS_REGION", "us-east-1")
        self.AGENT_NAME = os.getenv("AGENT_NAME", "estate-planning-agent")
        self.MODEL_ID = os.getenv("MODEL_ID", "global.anthropic.claude-sonnet-4-20250514-v1:0")

        # Cognito Configuration
        self.COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_9YpMeBgjH")
        self.COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "70fgkn9bg38jb4e84p9l0htfa4")
        self.COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

        # Gateway Configuration
        self.GATEWAY_URL: Optional[str] = os.getenv("GATEWAY_URL")
        self.M2M_PROVIDER_NAME = os.getenv("M2M_PROVIDER_NAME", "estate-planning-m2m-provider")

        # Discovery URL for Cognito
        self.DISCOVERY_URL = f"https://cognito-idp.{self.REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/openid-configuration"

    def validate(self) -> bool:
        """Validate required configuration"""
        required_vars = [
            self.COGNITO_CLIENT_SECRET,
            self.GATEWAY_URL
        ]
        return all(var is not None for var in required_vars)

    def validate_for_runtime(self) -> None:
        """Runtime validation with helpful error messages for container deployment"""
        missing_vars = []
        error_messages = []

        if not self.COGNITO_CLIENT_SECRET:
            missing_vars.append("COGNITO_CLIENT_SECRET")
            error_messages.append("- COGNITO_CLIENT_SECRET: Required for M2M authentication")

        if not self.GATEWAY_URL:
            missing_vars.append("GATEWAY_URL")
            error_messages.append("- GATEWAY_URL: AgentCore Gateway endpoint for tool access")

        if missing_vars:
            error_msg = f"""
Estate Planning Agent Configuration Error

Missing required environment variables:
{chr(10).join(error_messages)}

Container deployment requirements:
1. Ensure M2M credential provider is created in AgentCore Identity
2. Ensure AgentCore Gateway is deployed and accessible
3. Set environment variables in your AgentCore runtime configuration

Current configuration:
- Agent Name: {self.AGENT_NAME}
- Model: {self.MODEL_ID}
- Region: {self.REGION}
- Gateway URL: {'SET' if self.GATEWAY_URL else 'MISSING'}
- Client Secret: {'SET' if self.COGNITO_CLIENT_SECRET else 'MISSING'}
            """
            raise RuntimeError(error_msg)