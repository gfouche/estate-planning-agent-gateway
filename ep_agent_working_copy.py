
from strands import Agent
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import os
import json
import logging

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

def get_access_token(gateway_client, client_info):
    
    try:
        # Log client info (with sensitive data masked)
        safe_client_info = client_info.copy()
        if "client_secret" in safe_client_info:
            secret = safe_client_info["client_secret"]
            safe_client_info["client_secret"] = f"{secret[:5]}...{secret[-5:]}" if len(secret) > 10 else "***masked***"
        logging.info(f"Client info parameters: {json.dumps(safe_client_info)}")
        
        logging.info("Getting access token from Cognito")
        access_token = gateway_client.get_access_token_for_cognito(client_info)
        logging.info("Access token obtained successfully")
        return access_token, None
    except Exception as e:
        error_msg = f"Error accessing gateway: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return None, error_msg

def create_agent(config_path=None, initial_state=None) -> Agent:
  
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

    client = MCPClient(lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"}
    ))

    client.start()    
    logging.info("MCP Client created")

    tools = client.list_tools_sync()
    logging.info(f"Retrieved {len(tools)} tools from MCP gateway")
    
    # Get the system prompt
    system_prompt = get_system_prompt()
    
    # Add our state management tool
    all_tools = tools + [manage_state]
    logging.info(f"Added state management tool. Total tools: {len(all_tools)}")
    
    # Initialize with state if provided
    if initial_state:
        logging.info(f"Creating agent with initial state: {json.dumps(initial_state, indent=2)}")
        return Agent(
            model=model,
            tools=all_tools,
            state=initial_state,
            system_prompt=system_prompt
        )
    else:
        logging.info("Creating agent without initial state")
        return Agent(
            model=model,
            tools=all_tools,
            system_prompt=system_prompt
        )

def get_system_prompt():
    return """
You are an expert estate planning assistant. Your goal is to help users create and manage their estate plans, including wills, trusts, powers of attorney, and healthcare directives. You should provide clear, concise, and accurate information based on the user's needs and preferences.

IMPORTANT - STATE MANAGEMENT:
- You have access to the agent's state containing a structured Answers model with the user's estate planning information.
- When you receive new information from the user, update the state using the manage_state tool.
- The state contains these main components:
  1. "answers": A flat Pydantic model with all estate planning information using aliased fields
  2. "progress": Tracking of completion status for different sections
  3. "session_id": The unique ID for this conversation

STATE STRUCTURE:
The answers state has this flat structure with aliased fields:
- full_name (alias: client.fullName): The client's full name
- gender (alias: client.gender): The client's gender
- dob (alias: client.DOB): The client's date of birth
- aka (alias: client.AKA): Also known as names for the client
- city (alias: client.address.city): The client's city of residence
- state (alias: client.address.state): The client's state of residence
- email (alias: client.email): The client's email address

- marital_status (alias: client.maritalStatus): The client's marital status
- dom (alias: client.DOM): Date of marriage if applicable
- spouse_full_name (alias: spouse.fullName): The spouse's full name
- spouse_aka (alias: spouse.AKA): Also known as names for the spouse
- spouse_dob (alias: spouse.DOB): The spouse's date of birth

- has_children (alias: client.hasChildren): Whether the client has children
- children (alias: client.children): List of the client's children

- incapacity_primary_name (alias: representatives.incapacity.primary.fullName): Person to handle finances during incapacity
- incapacity_has_alternates (alias: representatives.incapacity.hasAlternates): Whether there are alternates
- incapacity_alternates (alias: representatives.incapacity.alternates): List of alternate incapacity representatives

- after_death_primary_name (alias: representatives.afterDeath.primary.fullName): Person to handle affairs after death
- after_death_has_alternates (alias: representatives.afterDeath.hasAlternates): Whether there are alternates
- after_death_alternates (alias: representatives.afterDeath.alternates): List of alternate after death representatives

- healthcare_primary_name (alias: representatives.healthcare.primary.fullName): Person to make healthcare decisions
- healthcare_has_alternates (alias: representatives.healthcare.hasAlternates): Whether there are alternates
- healthcare_alternates (alias: representatives.healthcare.alternates): List of alternate healthcare representatives

- has_guardians (alias: hasGuardians): Whether the client has designated guardians
- guardians (alias: guardians): List of guardians for dependents

- has_pet_provisions (alias: client.hasPetProvisions): Whether the client has provisions for pets
- pets (alias: client.pets): List of the client's pets
- pets_caretaker (alias: client.petsCaretaker): Designated caretaker for pets
- pets_care_amount (alias: client.petsCareAmount): Amount allocated for pet care

- maintain_in_home (alias: maintainInHome): End of life preference for maintaining in home
- remains_preference (alias: remainsPreference): Preference for remains

- has_specific_gifts (alias: hasSpecificGifts): Whether the client has specific gifts to bequeath
- specific_gifts (alias: specificGifts): List of specific gifts
- residuary_distribution (alias: residuaryDistribution): Residuary distribution preferences
- residuary_named_beneficiaries (alias: residuaryNamedBeneficiaries): Named beneficiaries for residuary distribution

USING THE MANAGE_STATE TOOL:
- To retrieve information, use the alias format: manage_state(key="client.fullName")
- To update information: manage_state(key="client.fullName", value="John Doe")
- To check progress: manage_state(key="progress.personalInfo")
- To update progress: manage_state(key="progress.personalInfo", value="completed")

PROGRESS TRACKING:
Track progress in these sections with these status values:
- "not_started": Section has not been addressed yet
- "in_progress": Currently collecting information for this section
- "completed": All necessary information for this section has been collected

ALWAYS update state when receiving new information and update the corresponding progress section.
"""

from strands import tool

@tool
def manage_state(key: str, value: str = None, agent: Agent = None) -> str:
    """
    A tool for managing the agent's state. Can get or set values in the Pydantic models.
    
    Args:
        key: The state key to get or set (e.g., "client.fullName" or "progress.personalInfo")
        value: The value to set. If None, will get the current value
        agent: The agent instance (automatically injected)
        
    Returns:
        A confirmation message or the current value
    """
    # Split the key into parts
    parts = key.split('.')
    
    # For get operations
    if value is None:
        try:
            # Simple case - top level key
            if len(parts) == 1:
                current_value = agent.state.get(key)
                return f"Current value for {key}: {current_value}"
            
            # Handle progress section
            elif parts[0] == 'progress':
                progress = agent.state.get('progress', {})
                if len(parts) == 2 and parts[1] in progress:
                    return f"Current value for {key}: {progress[parts[1]]}"
                else:
                    return f"Error: Invalid progress key {key}"
            
            # Handle aliased fields in the answers model
            else:
                # Get the answers object
                answers = agent.state.get('answers')
                if not isinstance(answers, Answers):
                    return f"Error: answers is not a valid Pydantic model"
                
                # Find the field with matching alias
                dotted_key = key  # The full dotted key is the alias
                for field_name, field in answers.__fields__.items():
                    if field.alias == dotted_key:
                        current_value = getattr(answers, field_name)
                        return f"Current value for {key}: {current_value}"
                
                # If we didn't find a matching alias
                return f"Error: No field with alias {key} found in answers model"
        
        except Exception as e:
            return f"Error accessing {key}: {str(e)}"
    
    # For set operations
    else:
        try:
            # Handle progress updates
            if parts[0] == 'progress':
                progress = agent.state.get('progress', {})
                
                # Update progress
                if len(parts) == 2 and parts[1] in ['personalInfo', 'familyInfo', 'representatives', 
                                                  'guardians', 'pets', 'endOfLife', 'distribution', 'completed']:
                    progress[parts[1]] = value
                    agent.state.set('progress', progress)
                    return f"Successfully set {key} to: {value}"
                else:
                    return f"Error: Invalid progress key {key}"
            
            # Handle session_id updates
            elif key == 'session_id':
                agent.state.set('session_id', value)
                return f"Successfully set session_id to: {value}"
            
            # Handle updates to the answers model using aliased keys
            else:
                # Get the answers object
                answers = agent.state.get('answers')
                if not isinstance(answers, Answers):
                    # Initialize if needed
                    answers = Answers()
                
                # Find the field with matching alias and update it
                dotted_key = key  # The full dotted key is the alias
                field_found = False
                
                for field_name, field in answers.__fields__.items():
                    if field.alias == dotted_key:
                        # Convert value to appropriate type if needed
                        field_found = True
                        setattr(answers, field_name, value)
                        break
                
                if not field_found:
                    return f"Error: No field with alias {key} found in answers model"
                
                # Update the full model in state
                agent.state.set('answers', answers)
                return f"Successfully set {key} to: {value}"
        
        except Exception as e:
            return f"Error setting {key}: {str(e)}"


class Progress(BaseModel):
    """Model for tracking progress through the estate planning process"""
    personalInfo: str = "not_started"
    familyInfo: str = "not_started"
    representatives: str = "not_started"
    guardians: str = "not_started"
    pets: str = "not_started"
    endOfLife: str = "not_started"
    distribution: str = "not_started"
    completed: str = "not_started"

class Answers(BaseModel):
    # Client information
    full_name: Optional[str] = Field(default="", alias="client.fullName", description="user's full name")
    gender: Optional[str] = Field(default="", alias="client.gender", description="user's gender")
    dob: Optional[str] = Field(default="", alias="client.DOB", description="user's date of birth")
    aka: Optional[str] = Field(default="", alias="client.AKA", description="user's also known as names")
    city: Optional[str] = Field(default="", alias="client.address.city", description="user's city")
    state: Optional[str] = Field(default="", alias="client.address.state", description="user's state")
    email: Optional[str] = Field(default="", alias="client.email", description="user's email")
    
    # Marriage information
    marital_status: Optional[str] = Field(default="", alias="client.maritalStatus", description="user's marital status")
    dom: Optional[str] = Field(default="", alias="client.DOM", description="user's date of marriage")
    spouse_full_name: Optional[str] = Field(default="", alias="spouse.fullName", description="spouse's full name")
    spouse_aka: Optional[str] = Field(default="", alias="spouse.AKA", description="spouse's also known as names")
    spouse_dob: Optional[str] = Field(default="", alias="spouse.DOB", description="spouse's date of birth")
    
    # Children
    has_children: Optional[str] = Field(default="", alias="client.hasChildren", description="whether user has children")
    children: Optional[List[Any]] = Field(default_factory=list, alias="client.children", description="user's children")
    
    # Representatives
    incapacity_primary_name: Optional[str] = Field(default="", alias="representatives.incapacity.primary.fullName", description="primary incapacity representative")
    incapacity_has_alternates: Optional[str] = Field(default="", alias="representatives.incapacity.hasAlternates", description="whether user has alternate incapacity representatives")
    incapacity_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.incapacity.alternates", description="user's alternate incapacity representatives")
    
    after_death_primary_name: Optional[str] = Field(default="", alias="representatives.afterDeath.primary.fullName", description="primary after death representative")
    after_death_has_alternates: Optional[str] = Field(default="", alias="representatives.afterDeath.hasAlternates", description="whether user has alternate after death representatives")
    after_death_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.afterDeath.alternates", description="user's alternate after death representatives")
    
    healthcare_primary_name: Optional[str] = Field(default="", alias="representatives.healthcare.primary.fullName", description="primary healthcare representative")
    healthcare_has_alternates: Optional[str] = Field(default="", alias="representatives.healthcare.hasAlternates", description="whether user has alternate healthcare representatives")
    healthcare_alternates: Optional[List[Any]] = Field(default_factory=list, alias="representatives.healthcare.alternates", description="user's alternate healthcare representatives")
    
    # Guardians
    has_guardians: Optional[str] = Field(default="", alias="hasGuardians", description="whether user has guardians for dependents")
    guardians: Optional[List[Any]] = Field(default_factory=list, alias="guardians", description="user's designated guardians")
    
    # Pets
    has_pet_provisions: Optional[str] = Field(default="", alias="client.hasPetProvisions", description="whether user has provisions for pets")
    pets: Optional[List[Any]] = Field(default_factory=list, alias="client.pets", description="user's pets")
    pets_caretaker: Optional[str] = Field(default="", alias="client.petsCaretaker", description="designated caretaker for user's pets")
    pets_care_amount: Optional[str] = Field(default="", alias="client.petsCareAmount", description="amount allocated for pet care")
    
    # End of life preferences
    maintain_in_home: Optional[str] = Field(default="", alias="maintainInHome", description="whether to maintain in home")
    remains_preference: Optional[str] = Field(default="", alias="remainsPreference", description="user's preference for remains")
    
    # Distribution
    has_specific_gifts: Optional[str] = Field(default="", alias="hasSpecificGifts", description="whether user has specific gifts")
    specific_gifts: Optional[List[Any]] = Field(default_factory=list, alias="specificGifts", description="user's specific gifts")
    residuary_distribution: Optional[str] = Field(default="", alias="residuaryDistribution", description="residuary distribution preferences")
    residuary_named_beneficiaries: Optional[List[Any]] = Field(default_factory=list, alias="residuaryNamedBeneficiaries", description="named beneficiaries for residuary distribution")
    
    class Config:
        populate_by_name = True
    
    def to_alias_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary using aliases as keys"""
        return self.model_dump(by_alias=True)
    
    def update_from_flat_dict(self, data: Dict[str, Any]) -> None:
        """Update the model from a flat dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_from_dotted_dict(self, data: Dict[str, Any]) -> None:
        """Update the model from a dictionary with dotted notation keys"""
        # Create a reverse lookup of aliases to attribute names
        alias_to_attr = {}
        for field_name, field in self.__fields__.items():
            if field.alias:
                alias_to_attr[field.alias] = field_name
        
        # Update attributes based on dotted notation keys
        for key, value in data.items():
            if key in alias_to_attr:
                setattr(self, alias_to_attr[key], value)

class SessionState(BaseModel):
    """Model representing the complete session state"""
    session_id: str
    answers: Answers = Field(default_factory=Answers)
    progress: Progress = Field(default_factory=Progress)

class SessionManager:
    """Manages session state for each user conversation using flat Pydantic models"""
    
    def __init__(self):
        self.sessions = {}  # Dictionary of session_id to SessionState
        logging.info("Session manager initialized with flat Pydantic models")
        
    def get_session_state(self, session_id: str):
        """Get the session state for a specific session ID"""
        if session_id not in self.sessions:
            # Create a new session state with default values
            self.sessions[session_id] = SessionState(session_id=session_id)
            logging.info(f"Created new session state for {session_id}")
        return self.sessions[session_id]
    
    def update_answers(self, session_id: str, answers_data: Dict[str, Any]) -> None:
        """Update answers in the session state from incoming flat dictionary"""
        session = self.get_session_state(session_id)
        
        # Determine if we're dealing with snake_case keys or dotted notation keys
        if any("." in key for key in answers_data.keys()):
            # Handle dotted notation keys
            for key, value in answers_data.items():
                # Find the corresponding field in our flat model
                for field_name, field in session.answers.__fields__.items():
                    if field.alias == key:
                        setattr(session.answers, field_name, value)
                        break
        else:
            # Handle snake_case keys (direct attributes of our model)
            session.answers.update_from_flat_dict(answers_data)
            
        logging.info(f"Updated answers for session {session_id}")
    
    def update_progress(self, session_id: str, progress_data: Dict[str, Any]) -> None:
        """Update progress tracking for a session"""
        session = self.get_session_state(session_id)
        for key, value in progress_data.items():
            if hasattr(session.progress, key):
                setattr(session.progress, key, value)
        logging.info(f"Updated progress for session {session_id}")
    
    def get_agent_state(self, session_id: str) -> Dict[str, Any]:
        """Get a dictionary representation of the session state for the agent"""
        session = self.get_session_state(session_id)
        
        # Convert answers to a dictionary with alias keys for compatibility
        answers_dict = session.answers.to_alias_dict()
        
        return {
            "session_id": session_id,
            "answers": answers_dict,
            "progress": session.progress.model_dump()
        }

app = BedrockAgentCoreApp()
# Initialize the session manager
session_manager = SessionManager()
# Agent will be created per session

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None

class AgentResponse(BaseModel):
    status: str = Field(description="success, error, or partial")
    message: str = Field(description="Human-readable response")
    tools_used: List[ToolResult] = Field(default_factory=list)
    action_required: bool = Field(default=False, description="Whether user action is needed")
    metadata: dict = Field(default_factory=dict, description="Additional context")
    answers: Answers = Field(default_factory=Answers, description="Extracted user information")

# Removed deep_merge_dicts as we're using Pydantic models directly

@app.entrypoint
def invoke(payload, context):
    """
    Main entrypoint for the agent. Processes user requests and manages state.
    
    Args:
        payload: Dictionary containing user input and potential answer updates
        context: Context information including session_id
        
    Returns:
        AgentResponse: Structured response with message and current answers state
    """
    user_message = payload["prompt"]
    incoming_answers = payload.get("answers", {})
    session_id = context.session_id

    if not session_id:
        raise Exception("Session ID is required in the context")
    
    logging.info(f"Received request with session ID: {session_id}")
    
    # Update session with incoming answers if any
    if incoming_answers:
        logging.info(f"Updating session with incoming answers")
        session_manager.update_answers(session_id, incoming_answers)
    
    # Get the agent state from the session
    agent_state = session_manager.get_agent_state(session_id)
    
    # Create agent instance with the current state
    agent = create_agent(initial_state=agent_state)
    
    # Process the user message
    response = agent(user_message)
    
    # Generate the structured response
    structured_result = agent.structured_output(
        AgentResponse,
        "Format the response as JSON"
    )
    
    # Get the message text from the response
    structured_result.message = str(response.message["content"][0]["text"])
    
    # Get the updated state from the agent
    updated_state = agent.state.get()
    
    # Check if we have updates to the answers or progress
    if updated_state:
        # Get the session state
        session_state = session_manager.get_session_state(session_id)
        
        # If answers were updated in the state, update the session
        if "answers" in updated_state and isinstance(updated_state["answers"], Answers):
            # The answers in state are already a Pydantic model
            session_state.answers = updated_state["answers"]
        
        # If progress was updated in the state, update the session
        if "progress" in updated_state:
            progress_data = updated_state["progress"]
            if isinstance(progress_data, dict):
                session_manager.update_progress(session_id, progress_data)
    
    # Get the latest session state
    session_state = session_manager.get_session_state(session_id)
    
    # Set the answers in the response
    structured_result.answers = session_state.answers
    
    # Add progress tracking to metadata
    structured_result.metadata["progress"] = session_state.progress.model_dump()
    
    return structured_result

if __name__ == "__main__":
    logging.info("Starting Estate Planning Agent Gateway")
    app.run()
    logging.info("Agent Gateway shutdown")
