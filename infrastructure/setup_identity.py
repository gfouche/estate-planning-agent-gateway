"""
Set up AgentCore Identity and credential providers
"""
import os
from bedrock_agentcore.services.identity import IdentityClient
from agent.config.settings import Settings

def setup_m2m_credential_provider():
    """Set up M2M credential provider for gateway access"""
    settings = Settings()
    
    if not settings.validate():
        raise ValueError("Missing required configuration. Check environment variables.")
    
    identity_client = IdentityClient(settings.REGION)
    
    # Create M2M credential provider
    provider_config = {
        "name": settings.M2M_PROVIDER_NAME,
        "credentialProviderVendor": "CustomOAuth2",
        "oauth2ProviderConfigInput": {
            "customOAuth2ProviderConfig": {
                "oauthDiscovery": {
                    "discoveryUrl": settings.DISCOVERY_URL
                },
                "clientId": settings.COGNITO_CLIENT_ID,
                "clientSecret": settings.COGNITO_CLIENT_SECRET
            }
        }
    }
    
    try:
        provider = identity_client.create_oauth2_credential_provider(provider_config)
        print(f"✅ Created M2M credential provider: {provider.get('providerArn')}")
        return provider
    except Exception as e:
        if "already exists" in str(e):
            print(f"✅ M2M credential provider already exists: {settings.M2M_PROVIDER_NAME}")
        else:
            raise e

if __name__ == "__main__":
    setup_m2m_credential_provider()