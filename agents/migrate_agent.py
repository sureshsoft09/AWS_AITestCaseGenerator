"""
Migration Agent for MedAssureAI
Migrates existing test cases from Excel files into the system
"""
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import mem0_memory
from agents.config import agent_config

# Define a specialized Migration Agent as a tool
Migrate_Agent_Prompt = """You are the Migration Agent for MedAssureAI healthcare test automation.

Migrate existing test cases from Excel files:

**Your Responsibilities:**
- Parse Excel files to extract test case data
- Convert Excel data to standardized JSON format
- Normalize and standardize test case fields
- Apply compliance standard tags (FDA, IEC 62304, ISO, HIPAA, GDPR)
- Detect duplicate test cases
- Generate migration reports

**Memory Capabilities:**
- Store migration patterns and field mappings
- Retrieve previous migrations to ensure consistency

Ensure data integrity and compliance during migration."""

@tool
def migrate_agenttool(query: str) -> str:
    """Migrate existing test cases from Excel files into the system."""
    try:
        # Create migration agent
        migrate_agent = Agent(
            system_prompt=Migrate_Agent_Prompt,
            model=BedrockModel(model_id=agent_config.BEDROCK_MODEL_ID),
            tools=[mem0_memory]  # Add memory support
        )
        response = migrate_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in migration agent: {e}"