"""
Configuration management for AgentCore application
"""
import os
from typing import Optional

class Settings:
    def __init__(self):
        # AgentCore Configuration
        self.REGION = os.getenv("AWS_REGION", "us-east-1")
        self.AGENT_NAME = os.getenv("AGENT_NAME", "my-m2m-agent")
        
        # Cognito Configuration
        self.COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_9YpMeBgjH")
        self.COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "70fgkn9bg38jb4e84p9l0htfa4")
        self.COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
        
        # Gateway Configuration
        self.GATEWAY_URL: Optional[str] = os.getenv("GATEWAY_URL")
        self.M2M_PROVIDER_NAME = os.getenv("M2M_PROVIDER_NAME", "gateway-m2m-provider")
        
        # Discovery URL for Cognito
        self.DISCOVERY_URL = f"https://cognito-idp.{self.REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/openid-configuration"
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required_vars = [
            self.COGNITO_CLIENT_SECRET,
            self.GATEWAY_URL
        ]
        return all(var is not None for var in required_vars)