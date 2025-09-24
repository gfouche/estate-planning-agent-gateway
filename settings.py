"""
Configuration management for AgentCore application
"""
import os
import pathlib
from typing import Optional, Any

# Import and load dotenv
try:
    from dotenv import load_dotenv
    # Look for .env file in the current directory and parent directories
    env_file = pathlib.Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️ No .env file found at {env_file}")
except ImportError:
    print("⚠️ python-dotenv not installed. Environment variables will only be loaded from system environment.")

class ConfigurationError(Exception):
    """Exception raised for configuration errors"""
    pass

class Settings:
    def __init__(self):
        """
        Initialize settings from environment variables
        
        Raises:
            ConfigurationError: If any required settings are missing
        """
        # Track required settings that are missing
        self._missing_required = []
        
        # AgentCore Configuration
        self.REGION = self._get_env("AWS_REGION", default="us-east-1", required=True)
        self.AGENT_NAME = self._get_env("AGENT_NAME", required=True)
        self.MODEL_ID = self._get_env("MODEL_ID", default="anthropic.claude-v2", required=False)
        
        # Cognito Configuration - Critical settings with no defaults
        self.COGNITO_USER_POOL_ID = self._get_env("COGNITO_USER_POOL_ID", required=True)
        self.COGNITO_CLIENT_ID = self._get_env("COGNITO_CLIENT_ID", required=True)
        self.COGNITO_CLIENT_SECRET = self._get_env("COGNITO_CLIENT_SECRET", required=True)
        
        # Gateway Configuration
        self.GATEWAY_URL = self._get_env("GATEWAY_URL", required=True)
        self.M2M_PROVIDER_NAME = self._get_env("M2M_PROVIDER_NAME", default="gateway-m2m-provider", required=False)
        
        # Derived settings
        if self.REGION and self.COGNITO_USER_POOL_ID:
            self.DISCOVERY_URL = f"https://cognito-idp.{self.REGION}.amazonaws.com/{self.COGNITO_USER_POOL_ID}/.well-known/openid-configuration"
        else:
            self.DISCOVERY_URL = None
            self._missing_required.append("DISCOVERY_URL (derived from REGION and COGNITO_USER_POOL_ID)")
        
        # Always validate immediately
        if self._missing_required:
            self._raise_missing_error()

    def _get_env(self, var_name: str, default: Any = None, required: bool = False) -> Any:
        """
        Get an environment variable with validation
        
        Args:
            var_name: Name of the environment variable
            default: Default value if not present
            required: Whether this variable is required
            
        Returns:
            Value of the environment variable or default
        """
        value = os.getenv(var_name, default)
        
        # Track missing required variables
        if required and value is None:
            self._missing_required.append(var_name)
            
        return value
    
    def _raise_missing_error(self) -> None:
        """Raise an error with details about missing configuration"""
        missing = ", ".join(self._missing_required)
        raise ConfigurationError(
            f"Missing required configuration: {missing}. "
            "Please set these environment variables before starting the application."
        )
    
    def validate(self) -> bool:
        """
        Check if all required configuration is present
        
        Returns:
            True if all required settings are present, False otherwise
        """
        return len(self._missing_required) == 0