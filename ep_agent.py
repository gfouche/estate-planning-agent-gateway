
from strands import Agent
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp
import logging
from dotenv import load_dotenv

#local imports
from settings import Settings
from gateway_client import WillGatewayClient

# Load environment variables from .env file for local development
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_agent(mcp_client) -> Agent:
       
    logging.info("Creating BedrockModel with Claude Sonnet us-east-1")
    model = BedrockModel(
        model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1"
    )

    tools = mcp_client.list_tools_sync()
    logging.info(f"Retrieved {len(tools)} tools from MCP gateway")
    
    return Agent(model=model, tools=tools)

# Global components - will be initialized based on configuration
settings: Optional[Settings] = None
gateway_client: Optional[WillGatewayClient] = None
agent: Optional[Agent] = None

def initialize_components():
    """Initialize components with graceful error handling for container deployment"""
    global settings, gateway_client, agent

    try:
        # Load settings
        settings = Settings()

        # Validate configuration for runtime
        settings.validate_for_runtime()
        # Initialize gateway client
        clientFactory = WillGatewayClient(
            gateway_url=settings.GATEWAY_URL,
            provider_name=settings.M2M_PROVIDER_NAME
        )

        gateway_client =  clientFactory.get_mcp_client()

        agent = create_agent(gateway_client)

        logging.info("DIY Will Agent initialized successfully")
        logging.info(f"   Agent: {settings.AGENT_NAME}")
        logging.info(f"   Model: {settings.MODEL_ID}")
        logging.info(f"   Gateway: {settings.GATEWAY_URL[:50]}...")

        return True

    except RuntimeError as e:
        logging.error(f"Configuration Error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Initialization Error: {str(e)}")
        return False

# Initialize components on module load
COMPONENTS_READY = initialize_components()

app = BedrockAgentCoreApp()

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

    user_message = payload["prompt"]
    user_answers = payload["answers"] if "answers" in payload else {}
    session_id = context.session_id

    if not session_id:
        raise Exception("Session ID is required in the context")
    
    logging.info(f"Received request with session ID: {session_id}")

    response = agent(user_message)
    structured_result = agent.structured_output(
        AgentResponse,
        "Format the response as JSON"
    )

    structured_result.message = str(response.message["content"][0]["text"])
    structured_result.answers = structured_result.answers.model_dump(by_alias=True)

    return structured_result

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
