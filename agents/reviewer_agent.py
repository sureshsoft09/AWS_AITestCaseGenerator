"""
Reviewer Agent for MedAssureAI
Analyzes requirements for ambiguities, duplicates, gaps, and compliance issues
"""
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import mem0_memory
from agents.config import agent_config

# Define a specialized Reviewer Agent as a tool
Reviewer_Agent_Prompt = """You are the Reviewer Agent for MedAssureAI healthcare test automation.

Analyze requirements documents for:
1. Ambiguities - vague terms, unclear scope, missing criteria
2. Duplicates - redundant or overlapping requirements  
3. Gaps - missing error handling, performance, security specs
4. Compliance - FDA, IEC 62304, ISO, HIPAA, GDPR standards

**Memory Capabilities:**
- Use mem0_memory to store important review findings and patterns
- Retrieve previous review insights to maintain consistency

Provide detailed analysis with specific recommendations for improvement."""

@tool
def reviewer_agenttool(query: str) -> str:
    """Analyze requirements for ambiguities, duplicates, gaps, and compliance issues."""
    try:
        # Create reviewer agent
        reviewer_agent = Agent(
            system_prompt=Reviewer_Agent_Prompt,
            model=BedrockModel(model_id=agent_config.BEDROCK_MODEL_ID),
            tools=[mem0_memory]  # Add memory support
        )
        response = reviewer_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in reviewer agent: {e}"