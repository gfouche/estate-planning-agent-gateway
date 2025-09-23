"""
Unit tests for infrastructure.setup_identity module
"""
import os
import unittest
from unittest.mock import patch, Mock, MagicMock

# Import the module we want to test
from setup_identity import setup_m2m_credential_provider
from settings import ConfigurationError

class TestSetupIdentity(unittest.TestCase):
    """Test cases for the setup_identity module"""
    
    @patch('setup_identity.IdentityClient')
    @patch('setup_identity.Settings')
    def test_setup_m2m_credential_provider_success(self, mock_settings_class, mock_identity_client_class):
        """Test successful creation of M2M credential provider"""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings._missing_required = []  # No missing required vars
        mock_settings.M2M_PROVIDER_NAME = "test-provider"
        mock_settings.REGION = "us-east-1"
        mock_settings.DISCOVERY_URL = "https://test-discovery-url"
        mock_settings.COGNITO_CLIENT_ID = "test-client-id"
        mock_settings.COGNITO_CLIENT_SECRET = "test-client-secret"
        
        # Setup mock identity client
        mock_identity_client = Mock()
        mock_identity_client_class.return_value = mock_identity_client
        mock_identity_client.create_oauth2_credential_provider.return_value = {
            "providerArn": "arn:aws:bedrock:us-east-1:123456789012:credential-provider/test-provider"
        }
        
        # Return mock settings from Settings class constructor
        mock_settings_class.return_value = mock_settings
        
        # Call the function
        result = setup_m2m_credential_provider()
        
        # Assertions
        mock_settings_class.assert_called_once()
        mock_identity_client_class.assert_called_once_with(mock_settings.REGION)
        
        # Verify the credential provider was created with correct configuration
        mock_identity_client.create_oauth2_credential_provider.assert_called_once()
        call_args = mock_identity_client.create_oauth2_credential_provider.call_args[0][0]
        self.assertEqual(call_args["name"], "test-provider")
        self.assertEqual(call_args["credentialProviderVendor"], "CustomOAuth2")
        self.assertEqual(call_args["oauth2ProviderConfigInput"]["customOAuth2ProviderConfig"]["clientId"], 
                         "test-client-id")
        
        # Verify the result
        self.assertEqual(result["providerArn"], 
                         "arn:aws:bedrock:us-east-1:123456789012:credential-provider/test-provider")
    
    @patch('setup_identity.IdentityClient')
    @patch('setup_identity.Settings')
    def test_setup_m2m_credential_provider_already_exists(self, mock_settings_class, mock_identity_client_class):
        """Test when M2M credential provider already exists"""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings._missing_required = []  # No missing required vars
        mock_settings.M2M_PROVIDER_NAME = "existing-provider"
        mock_settings.REGION = "us-east-1"
        
        # Setup mock identity client
        mock_identity_client = Mock()
        mock_identity_client_class.return_value = mock_identity_client
        
        # Make create_oauth2_credential_provider raise an exception with "already exists" message
        mock_identity_client.create_oauth2_credential_provider.side_effect = Exception(
            "ResourceConflictException: Credential Provider with name 'existing-provider' already exists"
        )
        
        # Return mock settings from Settings class constructor
        mock_settings_class.return_value = mock_settings
        
        # Call the function - it should handle the exception internally
        result = setup_m2m_credential_provider()
        
        # Assertions
        mock_settings_class.assert_called_once()
        mock_identity_client_class.assert_called_once_with(mock_settings.REGION)
        mock_identity_client.create_oauth2_credential_provider.assert_called_once()
        
        # Result should be None since we're handling the exception
        self.assertIsNone(result)
    
    @patch('setup_identity.Settings')
    def test_setup_m2m_credential_provider_validation_failure(self, mock_settings_class):
        """Test validation failure case"""
        # Setup mock settings with validation failing - construction will raise the error
        mock_settings_class.side_effect = ConfigurationError("Missing required configuration")
        
        # The function should raise ConfigurationError
        with self.assertRaises(ConfigurationError) as context:
            setup_m2m_credential_provider()
        
        # Check exception message
        self.assertIn("Missing required configuration", str(context.exception))
        
        # Assertions
        mock_settings_class.assert_called_once()
    
    @patch('setup_identity.IdentityClient')
    @patch('setup_identity.Settings')
    def test_setup_m2m_credential_provider_other_exception(self, mock_settings_class, mock_identity_client_class):
        """Test other exceptions are raised"""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings._missing_required = []  # No missing required vars
        mock_settings.M2M_PROVIDER_NAME = "test-provider"
        mock_settings.REGION = "us-east-1"
        
        # Setup mock identity client
        mock_identity_client = Mock()
        mock_identity_client_class.return_value = mock_identity_client
        
        # Make create_oauth2_credential_provider raise an exception
        test_exception = Exception("Some other AWS error")
        mock_identity_client.create_oauth2_credential_provider.side_effect = test_exception
        
        # Return mock settings from Settings class constructor
        mock_settings_class.return_value = mock_settings
        
        # The function should raise the exception
        with self.assertRaises(Exception) as context:
            setup_m2m_credential_provider()
        
        # Assertions
        mock_settings_class.assert_called_once()
        mock_identity_client_class.assert_called_once_with(mock_settings.REGION)
        mock_identity_client.create_oauth2_credential_provider.assert_called_once()
        self.assertEqual(context.exception, test_exception)


if __name__ == '__main__':
    unittest.main()