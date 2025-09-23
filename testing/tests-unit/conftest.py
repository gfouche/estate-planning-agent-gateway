"""
Pytest configuration file for unit tests
"""
import os
import sys
import pytest
from unittest.mock import patch

# Add the root directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

@pytest.fixture
def mock_settings():
    """Fixture for mocked Settings class"""
    with patch('settings.Settings') as mock_settings_class:
        mock_settings = mock_settings_class.return_value
        mock_settings.REGION = "us-east-1"
        mock_settings.AGENT_NAME = "test-agent"
        mock_settings.COGNITO_USER_POOL_ID = "us-east-1_testpool"
        mock_settings.COGNITO_CLIENT_ID = "test-client-id"
        mock_settings.COGNITO_CLIENT_SECRET = "test-client-secret"
        mock_settings.GATEWAY_URL = "https://test-gateway-url"
        mock_settings.M2M_PROVIDER_NAME = "test-provider"
        mock_settings.DISCOVERY_URL = "https://test-discovery-url"
        mock_settings.validate.return_value = True
        yield mock_settings

@pytest.fixture
def mock_identity_client():
    """Fixture for mocked IdentityClient"""
    with patch('bedrock_agentcore.services.identity.IdentityClient') as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.create_oauth2_credential_provider.return_value = {
            "providerArn": "arn:aws:bedrock:us-east-1:123456789012:credential-provider/test-provider"
        }
        yield mock_client