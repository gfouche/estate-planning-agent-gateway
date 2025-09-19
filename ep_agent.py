
from strands import Agent
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import os
import json
import logging
import time
from random import uniform

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_configuration(config_path):

    logging.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logging.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        return {"gateway_url": "", "cognito_info": {"client_info": {}}}

def get_access_token(gateway_client, client_info, max_retries=3):

    for attempt in range(max_retries):
        try:
            # Log client info (with sensitive data masked)
            safe_client_info = client_info.copy()
            if "client_secret" in safe_client_info:
                secret = safe_client_info["client_secret"]
                safe_client_info["client_secret"] = f"{secret[:5]}...{secret[-5:]}" if len(secret) > 10 else "***masked***"

            if attempt == 0:
                logging.info(f"Client info parameters: {json.dumps(safe_client_info)}")

            logging.info(f"Getting access token from Cognito (attempt {attempt + 1}/{max_retries})")
            access_token = gateway_client.get_access_token_for_cognito(client_info)
            logging.info("Access token obtained successfully")
            return access_token, None

        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error
            if ("429" in error_str or "Too Many Requests" in error_str) and attempt < max_retries - 1:
                # Exponential backoff with jitter
                backoff = (2 ** attempt) + uniform(0, 1)
                logging.warning(f"Rate limited on token fetch, retrying in {backoff:.2f} seconds...")
                time.sleep(backoff)
            else:
                error_msg = f"Error accessing gateway: {error_str}"
                logging.error(error_msg, exc_info=True)
                return None, error_msg

    # If we exhausted all retries
    return None, f"Failed to get access token after {max_retries} attempts"

def create_agent(config_path=None) -> Agent:
  
    # Initialize Gateway Client
    logging.info("Initializing Gateway Client")
    gateway_client = GatewayClient(region_name="us-east-1")
    
    # Load configuration
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    
    config = load_configuration(config_path)
    access_token = None
    gateway_url = None
    
    # Get access token and gateway URL
    if "cognito_info" in config and "client_info" in config["cognito_info"]:
        access_token, error = get_access_token(
            gateway_client, 
            config["cognito_info"]["client_info"]
        )
        
        if access_token:
            # Get gateway URL from configuration
            gateway_url = config.get("gateway_url", "https://your-gateway-url.amazonaws.com")
            logging.info(f"Using gateway URL: {gateway_url}")
    else:
        logging.error("Missing required configuration: cognito_info or client_info not found in config")
        return None
    
    if not access_token or not gateway_url:
        logging.error("Failed to initialize agent: Missing access token or gateway URL")
        return None
 
    logging.info("Creating BedrockModel with Claude Sonnet us-east-1")
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )

    # Create MCP client with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = MCPClient(lambda: streamablehttp_client(
                    gateway_url,
                    headers={"Authorization": f"Bearer {access_token}"}
            ))

            client.start()
            logging.info("MCP Client created")

            tools = client.list_tools_sync()
            logging.info(f"Retrieved {len(tools)} tools from MCP gateway")

            return Agent(
                model=model,
                tools=tools,
                system_prompt=get_system_prompt()
            )

        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "Too Many Requests" in error_str) and attempt < max_retries - 1:
                backoff = (2 ** attempt) + uniform(0, 1)
                logging.warning(f"Rate limited on MCP connection (attempt {attempt + 1}/{max_retries}), retrying in {backoff:.2f} seconds...")
                time.sleep(backoff)
            else:
                logging.error(f"Failed to create MCP client: {error_str}", exc_info=True)
                if attempt == max_retries - 1:
                    return None

    return None

def get_system_prompt():
    return """
You are an expert estate planning assistant. Your goal is to help users create and manage their estate plans, including wills, trusts, powers of attorney, and healthcare directives.

IMPORTANT: When users provide answers to estate planning questions, you MUST:
1. Extract the information from their responses
2. Use the update_answers tool to save their answers to the database with the EXACT format:
   {
     "userId": "user_identifier_here",
     "answerSet": {
       "responses": {
         "client.fullName": "their full name",
         "client.gender": "their gender",
         "client.DOB": "their date of birth",
         // ... other fields using dot notation like client.address.city, spouse.fullName, etc.
       }
     }
   }
3. Confirm that the information has been saved

The responses object MUST use dot notation for nested fields (e.g., "client.fullName", "client.address.city", "spouse.DOB").
Always save user responses as you collect them, don't wait until the end of the conversation.

You should provide clear, concise, and accurate information based on the user's needs and preferences.
"""  

app = BedrockAgentCoreApp()
agent = None  # Initialize lazily to prevent cold start bursts

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None

class Answers(BaseModel):
    full_name: Optional[str] = Field(default="", alias="client.fullName", description="user's full name")
    gender: Optional[str] = Field(default="", alias="client.gender", description="user's gender")
    dob: Optional[str] = Field(default="", alias="client.DOB", description="user's date of birth")
    aka: Optional[str] = Field(default="", alias="client.AKA", description="user's also known as names")
    city: Optional[str] = Field(default="", alias="client.address.city", description="user's city")
    state: Optional[str] = Field(default="", alias="client.address.state", description="user's state")
    email: Optional[str] = Field(default="", alias="client.email", description="user's email")
    
    marital_status: Optional[str] = Field(default="", alias="client.maritalStatus", description="user's marital status")
    dom: Optional[str] = Field(default="", alias="client.DOM", description="user's date of marriage")
    spouse_full_name: Optional[str] = Field(default="", alias="spouse.fullName", description="spouse's full name")
    spouse_aka: Optional[str] = Field(default="", alias="spouse.AKA", description="spouse's also known as names")
    spouse_dob: Optional[str] = Field(default="", alias="spouse.DOB", description="spouse's date of birth")
    
    has_children: Optional[str] = Field(default="", alias="client.hasChildren", description="whether user has children")
    children: Optional[List[Any]] = Field(default_factory=list, alias="client.children", description="user's children")
    
    incapacity_primary_name: Optional[str] = Field(default="", alias="representatives.incapacity.primary.fullName", description="primary incapacity representative")
    incapacity_has_alternates: Optional[str] = Field(default="", alias="representatives.incapacity.hasAlternates", description="whether user has alternate incapacity representatives")
    incapacity_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.incapacity.alternates", description="user's alternate incapacity representatives")
    
    after_death_primary_name: Optional[str] = Field(default="", alias="representatives.afterDeath.primary.fullName", description="primary after death representative")
    after_death_has_alternates: Optional[str] = Field(default="", alias="representatives.afterDeath.hasAlternates", description="whether user has alternate after death representatives")
    after_death_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.afterDeath.alternates", description="user's alternate after death representatives")
    
    healthcare_primary_name: Optional[str] = Field(default="", alias="representatives.healthcare.primary.fullName", description="primary healthcare representative")
    healthcare_has_alternates: Optional[str] = Field(default="", alias="representatives.healthcare.hasAlternates", description="whether user has alternate healthcare representatives")
    healthcare_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.healthcare.alternates", description="user's alternate healthcare representatives")
    
    has_guardians: Optional[str] = Field(default="", alias="hasGuardians", description="whether user has guardians for dependents")
    guardians: Optional[List[Any]] = Field(default_factory=list, alias="guardians", description="user's designated guardians")
    
    has_pet_provisions: Optional[str] = Field(default="", alias="client.hasPetProvisions", description="whether user has provisions for pets")
    pets: Optional[List[Any]] = Field(default_factory=list, alias="client.pets", description="user's pets")
    pets_caretaker: Optional[str] = Field(default="", alias="client.petsCaretaker", description="designated caretaker for user's pets")
    pets_care_amount: Optional[str] = Field(default="", alias="client.petsCareAmount", description="amount allocated for pet care")
    
    maintain_in_home: Optional[str] = Field(default="", alias="maintainInHome", description="whether to maintain in home")
    remains_preference: Optional[str] = Field(default="", alias="remainsPreference", description="user's preference for remains")
    
    has_specific_gifts: Optional[str] = Field(default="", alias="hasSpecificGifts", description="whether user has specific gifts")
    specific_gifts: Optional[List[Any]] = Field(default_factory=list, alias="specificGifts", description="user's specific gifts")
    
    residuary_distribution: Optional[str] = Field(default="", alias="residuaryDistribution", description="residuary distribution preferences")
    residuary_named_beneficiaries: Optional[List[Any]] = Field(default_factory=list, alias="residuaryNamedBeneficiaries", description="named beneficiaries for residuary distribution")


class AgentResponse(BaseModel):
    status: str = Field(description="success, error, or partial")
    message: str = Field(description="Human-readable response")
    tools_used: List[ToolResult] = Field(default_factory=list)
    action_required: bool = Field(default=False, description="Whether user action is needed")
    metadata: dict = Field(default_factory=dict, description="Additional context")
    answers: Answers = Field(default_factory=Answers, description="Extracted user information")

@app.entrypoint
def invoke(payload, context):
    global agent

    # Lazy initialization to prevent cold start token burst
    if agent is None:
        logging.info("Agent not initialized, creating new agent instance")
        agent = create_agent()
        if not agent:
            raise Exception("Failed to initialize agent")
        logging.info("Agent initialized successfully")

    user_message = payload["prompt"]
    user_answers = payload["answers"] if "answers" in payload else {}
    session_id = context.session_id

    if not session_id:
        raise Exception("Session ID is required in the context")

    logging.info(f"Received request with session ID: {session_id}")

    # First, let the agent process the message and use tools
    response = agent(user_message)

    # Create a structured response
    structured_result = AgentResponse(
        status="success",
        message="",
        tools_used=[],
        action_required=False,
        metadata={},
        answers=Answers()
    )

    # Extract the message from the response
    try:
        if hasattr(response, 'message') and response.message:
            if isinstance(response.message, dict) and "content" in response.message:
                content = response.message["content"]
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and "text" in content[0]:
                        structured_result.message = str(content[0]["text"])
                    else:
                        structured_result.message = str(content[0])
            else:
                structured_result.message = str(response.message)
        else:
            structured_result.message = str(response) if response else "Processing complete"
    except Exception as e:
        logging.warning(f"Could not extract message from response: {e}")
        structured_result.message = "Response processed"

    # Check if any tools were used
    if hasattr(response, 'tools_used'):
        for tool in response.tools_used:
            structured_result.tools_used.append(ToolResult(
                tool_name=tool.get('name', 'unknown'),
                success=True,
                data=tool.get('result', None)
            ))

    # Convert to dict with aliased field names for DynamoDB
    result_dict = structured_result.model_dump()
    result_dict["answers"] = structured_result.answers.model_dump(by_alias=True)

    return result_dict

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
