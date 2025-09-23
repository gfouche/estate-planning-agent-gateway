"""
Agent factory for creating and configuring agent instances
"""
from strands import Agent
from strands.models import BedrockModel

def create_agent(model_id, region_name):
    """
    Factory function to create a Strands Agent with a BedrockModel
    
    Args:
        model_id (str): The Bedrock model ID to use
        region_name (str): The AWS region name where the model is deployed
        
    Returns:
        Agent: Configured Strands agent with the specified model
    """
    model = BedrockModel(
        model_id=model_id,
        region_name=region_name
    )
    return Agent(model=model)