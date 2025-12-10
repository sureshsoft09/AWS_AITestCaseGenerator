"""
Enhancement Agent for MedAssureAI
Refactors and improves existing use cases and test cases
"""
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import mem0_memory
from agents.config import agent_config

# Define a specialized Enhancement Agent as a tool
Enhance_Agent_Prompt = """You are the Enhancement Agent for MedAssureAI healthcare test automation.

Refactor and improve existing use cases and test cases:

**Your Responsibilities:**
- Improve clarity and completeness
- Add missing test steps or scenarios
- Enhance acceptance criteria
- Update preconditions/postconditions
- Refine expected results
- Add edge cases

**Memory Capabilities:**
- Store enhancement patterns and best practices
- Retrieve previous improvements to ensure consistency

Preserve compliance mappings and traceability links while enhancing artifacts."""

@tool
def enhance_agenttool(query: str) -> str:
    """Refactor and improve existing use cases and test cases."""
    try:
        # Create enhancement agent
        enhance_agent = Agent(
            system_prompt=Enhance_Agent_Prompt,
            model=BedrockModel(model_id=agent_config.BEDROCK_MODEL_ID),
            tools=[mem0_memory]  # Add memory support
        )
        response = enhance_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in enhancement agent: {e}"