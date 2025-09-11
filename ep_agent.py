from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

model = BedrockModel(
            model_id="global.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name="us-east-1"
        )

app = BedrockAgentCoreApp()
agent = Agent(model=model)

@app.entrypoint
def invoke(payload):
    """Your AI agent function"""
    user_message = payload.get("prompt", "Hello! How can I help you today?")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()