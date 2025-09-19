"""
Estate Planning Agent API Gateway
Provides API endpoints for interacting with the estate planning agent.
This implementation uses Strands with AWS Bedrock for agent functionality 
and AgentCore for hosting.
"""

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent, Message
from strands.models import BedrockModel
from typing import Dict, Any, List, Optional
import uuid
import os
import sys
import json
from dotenv import load_dotenv

# Import local modules
from agent.agent_factory import create_agent
from workflow.estate_workflow import EstateWorkflow
from storage.s3_storage import create_s3_storage

# Load environment variables from .env file
load_dotenv()

# System prompt for the estate planning agent
SYSTEM_PROMPT = """
You are a professional estate planning assistant designed to help clients create a simple will. 
Your goal is to collect all necessary information in a conversational manner, organizing questions 
into small, logical groups.

Follow this structured workflow to gather information:

1. CLIENT INFORMATION:
   - Full legal name
   - Date of birth
   - Current address
   - Contact information (phone, email)

2. MARITAL STATUS:
   - Current marital status
   - If married:
     - Spouse's full legal name
     - Spouse's date of birth
     - Date of marriage
     - Any prenuptial agreements

3. FAMILY INFORMATION:
   - Children (for each):
     - Full legal names
     - Dates of birth
     - Whether they are biological, adopted, or stepchildren
   - Other dependents or family members to include

4. ASSETS:
   - Real estate properties
   - Bank accounts and investments
   - Retirement accounts
   - Life insurance policies
   - Valuable personal property (vehicles, jewelry, art, etc.)
   - Business interests

5. DISTRIBUTION OF ASSETS:
   - Primary beneficiaries and what they should receive
   - Contingent beneficiaries
   - Specific bequests (particular items to specific people)
   - Any disinheritance intentions

6. GUARDIANSHIP:
   - For minor children, who should be named guardian
   - Alternate guardian options

7. EXECUTOR APPOINTMENT:
   - Who should be named executor of the will
   - Alternate executor options

8. ADDITIONAL CONSIDERATIONS:
   - Funeral and burial wishes
   - Charitable giving
   - Pet care
   - Digital assets

Always be respectful, patient, and professional. Ask questions one small group at a time, and 
confirm understanding before moving to the next topic. Explain legal terms in simple language.
Remember that this information is sensitive and confidential.
"""

# Session management configuration
DEFAULT_SESSION_ID = os.environ.get("DEFAULT_SESSION_ID", "estate-planning-session")
SESSION_STORAGE_TYPE = os.environ.get("SESSION_STORAGE_TYPE", "file").lower()

# S3 configuration (used when SESSION_STORAGE_TYPE=s3)
S3_BUCKET_NAME = os.environ.get("SESSION_S3_BUCKET", "estate-planning-sessions")
S3_PREFIX = os.environ.get("SESSION_S3_PREFIX", "sessions")

# File storage configuration (used when SESSION_STORAGE_TYPE=file)
FILE_STORAGE_DIR = os.environ.get("FILE_STORAGE_DIR", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions"))

# AWS region for S3 (if using S3 storage)
AWS_REGION = os.environ.get("AWS_REGION")

print(f"Using {SESSION_STORAGE_TYPE} session storage")

# We'll create the agent in the invoke function with the appropriate session ID

# Create BedrockAgentCoreApp instance with configuration from agent_config.json
# AgentCore will look for agent_config.json by default
app = BedrockAgentCoreApp()

# Define sections of the estate planning workflow
WORKFLOW_SECTIONS = [
    "CLIENT_INFORMATION",
    "MARITAL_STATUS",
    "FAMILY_INFORMATION",
    "ASSETS",
    "DISTRIBUTION_OF_ASSETS",
    "GUARDIANSHIP",
    "EXECUTOR_APPOINTMENT",
    "ADDITIONAL_CONSIDERATIONS",
    "REVIEW_AND_COMPLETION"
]

# Helper function to extract client data from metadata
def extract_client_data(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured client data from agent's metadata.
    This can be used to generate documents later.
    """
    client_data = metadata.get("client_data", {})
    return client_data

@app.entrypoint
def invoke(payload: Dict[Any, Any]):
    """Estate planning agent function that maintains conversation state"""
    
    try:
        # Extract the user message
        user_message = payload.get("prompt", "Hello! Let's get started on your will.")
        
        # Get or create a session ID for this conversation
        # Use either provided session_id or the default from environment
        session_id = payload.get("session_id", os.environ.get("DEFAULT_SESSION_ID", str(uuid.uuid4())))
        
        # Create an agent with the specified session ID
        # This ensures we're using the proper session storage
        agent = create_agent(session_id)
        
        # Track the request in logs
        print(f"Processing request for session {session_id}")
        
        # Initialize or update metadata for tracking will creation progress
        metadata = {}
        
        # First try to get metadata from agent state
        try:
            # Check if agent.state is a dict-like object
            if hasattr(agent.state, "get"):
                metadata = agent.state.get("estate_planning") or {}
            elif hasattr(agent.state, "estate_planning"):
                # Handle as an attribute
                metadata = getattr(agent.state, "estate_planning", {})
        except (AttributeError, TypeError):
            # State isn't accessible as expected
            print("Warning: Could not access agent.state directly")
            
        # If metadata is still empty or missing key structures, initialize it
        if not metadata or not metadata.get("client_state"):
            print(f"Creating new metadata for session: {session_id}")
            metadata = {
                "client_state": {"current_section": "CLIENT_INFORMATION", "progress": 0},
                "client_data": {},
                "conversation_start_time": str(uuid.uuid1()),  # For tracking conversation duration
                "completed_sections": []
            }
            # Set state safely
            try:
                if isinstance(agent.state, dict):
                    agent.state["estate_planning"] = metadata
                elif hasattr(agent.state, "set"):
                    agent.state.set("estate_planning", metadata)
                elif hasattr(agent.state, "estate_planning"):
                    setattr(agent.state, "estate_planning", metadata)
            except Exception:
                # Log error or handle gracefully
                pass
        
        # Track progress through the will creation workflow
        client_state = metadata.get("client_state", {})
        current_section = client_state.get("current_section", "CLIENT_INFORMATION")
        
        # Process the user message and get a response
        try:
            # Create a proper Message object to leverage Strands fully
            message = Message(role="user", content=user_message)
            
            # Process the message using the agent
            result = agent(message)
            
            # Log the interaction
            print(f"Successfully processed message for session {session_id}")
        except Exception as e:
            # Check for S3 session errors
            if "Failed to write S3 object" in str(e) or "S3SessionManager" in str(e):
                print(f"S3 SESSION ERROR: {str(e)}")
                print(f"Running S3SessionManager diagnostics to help identify the issue...")
                
                # Import and run our S3 diagnostics that uses S3SessionManager directly
                try:
                    from diagnostics import diagnose_s3_session
                    diagnose_s3_session(
                        bucket_name=S3_BUCKET_NAME,
                        prefix=S3_PREFIX,
                        region_name=AWS_REGION
                    )
                except ImportError:
                    print("Could not import diagnostics module. Make sure it's properly installed.")
                except Exception as diag_error:
                    print(f"Error running diagnostics: {str(diag_error)}")
                
                # Provide clear next steps
                print(f"Next steps to resolve S3 issues:")
                print(f"1. Check that your AWS credentials are correctly set")
                print(f"2. Verify the bucket {S3_BUCKET_NAME} exists and is accessible")
                print(f"3. Ensure your IAM role/user has the necessary S3 permissions")
                print(f"4. Check if the region configuration matches your bucket's region")
                
                # Re-raise the error for proper error handling
                raise
            else:
                # For other types of errors
                raise
        
        # Update workflow progress based on conversation
        # Extract message content safely (handling if result.message is a dict or string)
        message_text = ""
        try:
            if isinstance(result.message, dict):
                # Try to extract text from common dictionary formats
                if "content" in result.message:
                    content = result.message["content"]
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                message_text += item["text"] + " "
                    else:
                        message_text = str(content)
                elif "text" in result.message:
                    message_text = result.message["text"]
                else:
                    # Fallback to string representation
                    message_text = str(result.message)
            else:
                # If it's already a string or has a string representation
                message_text = str(result.message)
        except Exception:
            # Fallback if we can't extract properly
            message_text = ""
            
        message_lower = message_text.lower()
        
        # Safely access state again
        try:
            if hasattr(agent.state, "get"):
                metadata = agent.state.get("estate_planning") or {}
            elif hasattr(agent.state, "estate_planning"):
                metadata = getattr(agent.state, "estate_planning", {})
            # Add a debug log to track state retrieval
            print(f"Retrieved metadata state with sections: {metadata.get('completed_sections', [])}")
        except (AttributeError, TypeError) as e:
            print(f"Error accessing agent state: {str(e)}")
            metadata = {}
            
        completed_sections = metadata.get("completed_sections", [])
        client_data = metadata.get("client_data", {})
        
        # More sophisticated section transition logic
        section_transitions = {
            "CLIENT_INFORMATION": {
                "keywords": ["marital", "married", "single", "divorced", "widowed"],
                "next": "MARITAL_STATUS",
                "data_keys": ["name", "dob", "address", "contact", "citizenship"]
            },
            "MARITAL_STATUS": {
                "keywords": ["children", "dependents", "family"],
                "next": "FAMILY_INFORMATION",
                "data_keys": ["marital_status", "spouse_name", "marriage_date"]
            },
            "FAMILY_INFORMATION": {
                "keywords": ["assets", "property", "accounts", "investments"],
                "next": "ASSETS",
                "data_keys": ["children", "dependents"]
            },
            "ASSETS": {
                "keywords": ["beneficiaries", "inherit", "distribute", "bequest"],
                "next": "DISTRIBUTION_OF_ASSETS",
                "data_keys": ["real_estate", "bank_accounts", "investments", "valuable_items"]
            },
            "DISTRIBUTION_OF_ASSETS": {
                "keywords": ["guardian", "minor", "care for children"],
                "next": "GUARDIANSHIP",
                "data_keys": ["primary_beneficiaries", "contingent_beneficiaries", "specific_bequests"]
            },
            "GUARDIANSHIP": {
                "keywords": ["executor", "personal representative", "administer"],
                "next": "EXECUTOR_APPOINTMENT",
                "data_keys": ["guardian", "alternate_guardian"]
            },
            "EXECUTOR_APPOINTMENT": {
                "keywords": ["funeral", "burial", "charitable", "donation", "pets", "digital"],
                "next": "ADDITIONAL_CONSIDERATIONS",
                "data_keys": ["executor", "alternate_executor"]
            },
            "ADDITIONAL_CONSIDERATIONS": {
                "keywords": ["review", "complete", "finalize", "summary"],
                "next": "REVIEW_AND_COMPLETION",
                "data_keys": ["funeral_wishes", "charitable_giving", "pet_care", "digital_assets"]
            },
            "REVIEW_AND_COMPLETION": {
                "keywords": [],
                "next": None,
                "data_keys": []
            }
        }
        
        # Check if we should advance to the next section
        current_section_info = section_transitions.get(current_section, {})
        for keyword in current_section_info.get("keywords", []):
            if keyword in message_lower:
                # Mark current section as completed
                if current_section not in completed_sections:
                    completed_sections.append(current_section)
                
                # Move to next section
                next_section = current_section_info.get("next")
                if next_section:
                    current_section = next_section
                    break
        
        # Update progress percentage based on completed sections
        progress = (len(completed_sections) / (len(WORKFLOW_SECTIONS) - 1)) * 100 if WORKFLOW_SECTIONS else 0
        
        # Store updated state
        client_state["current_section"] = current_section
        client_state["progress"] = progress
        metadata["client_state"] = client_state
        metadata["completed_sections"] = completed_sections
        
        # Safely update state and ensure it's properly persisted
        try:
            if isinstance(agent.state, dict):
                agent.state["estate_planning"] = metadata
            elif hasattr(agent.state, "set"):
                agent.state.set("estate_planning", metadata)
            elif hasattr(agent.state, "estate_planning"):
                setattr(agent.state, "estate_planning", metadata)
                
            # Force persistence by explicitly saving state if possible
            if hasattr(agent, "session_manager") and hasattr(agent.session_manager, "save_agent"):
                agent.session_manager.save_agent(agent)
            print(f"Updated metadata for session: {session_id}, current section: {current_section}")
        except Exception as e:
            # Log the specific error for debugging
            print(f"Error updating agent state: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        # Return the agent's response with enriched metadata
        # Ensure we return a properly formatted message
        response_message = message_text if message_text else "I'm here to help you create a will."
        
        return {
            "result": response_message,
            "session_id": session_id,
            "current_section": current_section,
            "progress": progress,
            "completed_sections": completed_sections,
            "answers": {}
        }
    except Exception as e:
        # Return an error response with diagnostic information
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in invoke function: {str(e)}")
        print(f"Error details: {error_details}")
        
        return {
            "result": "I apologize, but I encountered an error while processing your request. The estate planning agent is currently experiencing technical difficulties.",
            "error": str(e),
            "error_details": error_details
        }

if __name__ == "__main__":
    import sys
    
    # Check if diagnostic mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose-s3":
        print("Running S3SessionManager diagnostic checks...")
        from diagnostics import diagnose_s3_session
        diagnose_s3_session(
            bucket_name=S3_BUCKET_NAME,
            prefix=S3_PREFIX,
            region_name=AWS_REGION
        )
    else:
        app.run()
