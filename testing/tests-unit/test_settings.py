"""
Unit tests for the Settings class
"""
import os
import unittest
from unittest.mock import patch

from ep_agent.config.settings import Settings, ConfigurationError

class TestSettings(unittest.TestCase):
    """Test cases for the Settings class"""

    def test_default_values_for_optional_settings(self):
        """Test that default values are set correctly for non-required settings"""
        # Provide required settings to avoid validation errors
        test_env = {
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
            "COGNITO_CLIENT_SECRET": "test-secret",
            "GATEWAY_URL": "https://test-gateway.example.com",
            "AGENT_NAME": "test-agent"
        }
        
        with patch.dict(os.environ, test_env):
            settings = Settings()
            
            # Check default values for optional settings
            self.assertEqual(settings.REGION, "us-east-1")  # Default provided
            self.assertEqual(settings.AGENT_NAME, "test-agent")  # Provided in test_env
            self.assertEqual(settings.M2M_PROVIDER_NAME, "gateway-m2m-provider")  # Default provided
            
            # Check the derived discovery URL
            expected_discovery_url = f"https://cognito-idp.us-east-1.amazonaws.com/test-pool-id/.well-known/openid-configuration"
            self.assertEqual(settings.DISCOVERY_URL, expected_discovery_url)

    def test_environment_override(self):
        """Test that environment variables override default values"""
        test_env = {
            "AWS_REGION": "eu-west-1",
            "AGENT_NAME": "test-agent",
            "COGNITO_USER_POOL_ID": "eu-west-1_TestPool",
            "COGNITO_CLIENT_ID": "test-client-id",
            "COGNITO_CLIENT_SECRET": "test-client-secret",
            "GATEWAY_URL": "https://test-gateway.example.com",
            "M2M_PROVIDER_NAME": "test-provider"
        }
        
        with patch.dict(os.environ, test_env):
            settings = Settings()
            
            # Check that values were overridden
            self.assertEqual(settings.REGION, "eu-west-1")
            self.assertEqual(settings.AGENT_NAME, "test-agent")
            self.assertEqual(settings.COGNITO_USER_POOL_ID, "eu-west-1_TestPool")
            self.assertEqual(settings.COGNITO_CLIENT_ID, "test-client-id")
            self.assertEqual(settings.COGNITO_CLIENT_SECRET, "test-client-secret")
            self.assertEqual(settings.GATEWAY_URL, "https://test-gateway.example.com")
            self.assertEqual(settings.M2M_PROVIDER_NAME, "test-provider")
            
            # Check that the discovery URL uses the overridden values
            expected_discovery_url = f"https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_TestPool/.well-known/openid-configuration"
            self.assertEqual(settings.DISCOVERY_URL, expected_discovery_url)

    def test_validation_success(self):
        """Test that validation succeeds when all required variables are present"""
        test_env = {
            "AWS_REGION": "us-east-1",
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
            "COGNITO_CLIENT_SECRET": "test-secret",
            "GATEWAY_URL": "https://test-gateway.example.com",
            "AGENT_NAME": "test-agent"
        }
        
        with patch.dict(os.environ, test_env):
            # Should not raise an exception when all required variables are present
            settings = Settings()
            self.assertTrue(settings.validate())

    def test_validation_failure_missing_client_secret(self):
        """Test that validation fails when client secret is missing"""
        test_env = {
            "AWS_REGION": "us-east-1",
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
            # Missing COGNITO_CLIENT_SECRET
            "GATEWAY_URL": "https://test-gateway.example.com"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Should raise an error by default
            with self.assertRaises(ConfigurationError) as context:
                Settings()
                
            self.assertIn("COGNITO_CLIENT_SECRET", str(context.exception))

    def test_validation_failure_missing_gateway_url(self):
        """Test that validation fails when gateway URL is missing"""
        test_env = {
            "AWS_REGION": "us-east-1",
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
            "COGNITO_CLIENT_SECRET": "test-secret"
            # Missing GATEWAY_URL
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Should raise an error by default
            with self.assertRaises(ConfigurationError) as context:
                Settings()
                
            self.assertIn("GATEWAY_URL", str(context.exception))
    
    def test_validation_failure_missing_multiple_required(self):
        """Test that validation fails when multiple required variables are missing"""
        with patch.dict(os.environ, {}, clear=True):
            # Should raise an error by default
            with self.assertRaises(ConfigurationError) as context:
                Settings()
                
            error_message = str(context.exception)
            self.assertIn("COGNITO_CLIENT_SECRET", error_message)
            self.assertIn("GATEWAY_URL", error_message)
            self.assertIn("COGNITO_USER_POOL_ID", error_message)
            self.assertIn("COGNITO_CLIENT_ID", error_message)
    
    def test_missing_agent_name(self):
        """Test that validation fails when AGENT_NAME is missing"""
        test_env = {
            "AWS_REGION": "us-east-1",
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
            "COGNITO_CLIENT_SECRET": "test-secret",
            "GATEWAY_URL": "https://test-gateway.example.com"
            # Missing AGENT_NAME
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Should raise an error when AGENT_NAME is missing
            with self.assertRaises(ConfigurationError) as context:
                Settings()
                
            self.assertIn("AGENT_NAME", str(context.exception))
            
    def test_missing_critical_settings(self):
        """Test that validation fails when critical settings are missing"""
        test_env = {
            "AWS_REGION": "us-east-1",
            # Missing COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID
            "COGNITO_CLIENT_SECRET": "test-secret",
            "GATEWAY_URL": "https://test-gateway.example.com"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            # Should raise an error when critical settings are missing
            with self.assertRaises(ConfigurationError) as context:
                Settings()
                
            error_message = str(context.exception)
            self.assertIn("COGNITO_USER_POOL_ID", error_message)
            self.assertIn("COGNITO_CLIENT_ID", error_message)


if __name__ == "__main__":
    unittest.main()