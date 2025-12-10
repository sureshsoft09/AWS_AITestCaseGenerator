"""
Test Generator Agent for MedAssureAI
Generates test artifacts (epics, features, use cases, test cases) from requirements
"""
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import mem0_memory
from agents.config import agent_config

# Define a specialized Test Generator Agent as a tool
TestGenerator_Agent_Prompt = """You are the Test Generator Agent for MedAssureAI healthcare test automation.

Generate comprehensive test artifacts from requirements:

**Artifact Hierarchy:**
1. Epics - High-level themes grouping related functionality
2. Features - Functional groupings within epics
3. Use Cases - User scenarios with acceptance criteria
4. Test Cases - Specific test steps and expected results

**Memory Capabilities:**
- Store generated test patterns and templates for reuse
- Retrieve previous test artifacts to maintain consistency

Apply compliance standards (FDA, IEC 62304, ISO, HIPAA, GDPR) and maintain traceability."""

@tool
def testgenerator_agenttool(query: str) -> str:
    """Generate test artifacts (epics, features, use cases, test cases) from requirements."""
    try:
        # Create test generator agent
        test_generator_agent = Agent(
            system_prompt=TestGenerator_Agent_Prompt,
            model=BedrockModel(model_id=agent_config.BEDROCK_MODEL_ID),
            tools=[mem0_memory]  # Add memory support
        )
        response = test_generator_agent(query)
        return str(response)
    except Exception as e:
        return f"Error in test generator agent: {e}"