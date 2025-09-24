"""
Set up AgentCore Identity and credential providers
"""
import os
import logging
from bedrock_agentcore.services.identity import IdentityClient
from settings import Settings

def setup_m2m_credential_provider():
    """
    Set up M2M credential provider for gateway access
    
    Raises:
        ConfigurationError: If required configuration is missing
    """
    # Initialize settings - this will validate and raise any configuration errors
    settings = Settings()
    
    identity_client = IdentityClient(settings.REGION)
    
    # Create M2M credential provider
    provider_config = {
        "name": settings.M2M_PROVIDER_NAME,
        "credentialProviderVendor": "CustomOauth2",
        "oauth2ProviderConfigInput": {
            "customOauth2ProviderConfig": {
                "oauthDiscovery": {
                    "discoveryUrl": settings.DISCOVERY_URL
                },
                "clientId": settings.COGNITO_CLIENT_ID,
                "clientSecret": settings.COGNITO_CLIENT_SECRET
            }
        }
    }
    
    logging.info("Creating OAuth2 credential provider...")
    try:
        provider = identity_client.create_oauth2_credential_provider(provider_config)
        logging.info(f"✅ Created M2M credential provider: {provider.get('providerArn')}")
        return provider
    except Exception as e:
        if "already exists" in str(e):
            logging.info(f"✅ M2M credential provider already exists: {settings.M2M_PROVIDER_NAME}")
            # Return existing provider or get it from AWS
            return {"name": settings.M2M_PROVIDER_NAME, "status": "already_exists"}
        else:
            logging.error(f"Failed to create OAuth2 credential provider: {str(e)}")
            raise e

if __name__ == "__main__":
    setup_m2m_credential_provider()