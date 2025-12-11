"""
Orchestrator Agent for MedAssureAI
Coordinates multiple specialized agents using Strands framework
Exposes agents as FastAPI service
"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from strands import Agent, tool
from strands.models import BedrockModel

import threading
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

from agents.config import agent_config
from agents.logger import logger

# Configure mem0 environment variables before importing
import os
os.environ["MEM0_LLM_PROVIDER"] = os.getenv("MEM0_LLM_PROVIDER", "aws_bedrock")
os.environ["MEM0_LLM_MODEL"] = os.getenv("MEM0_LLM_MODEL", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
os.environ["MEM0_EMBEDDER_PROVIDER"] = os.getenv("MEM0_EMBEDDER_PROVIDER", "aws_bedrock")
os.environ["MEM0_EMBEDDER_MODEL"] = os.getenv("MEM0_EMBEDDER_MODEL", "amazon.titan-embed-text-v2:0")

from strands_tools import mem0_memory

from agents.reviewer_agent import reviewer_agenttool
from agents.test_generator_agent import testgenerator_agenttool
from agents.enhance_agent import enhance_agenttool
from agents.migrate_agent import migrate_agenttool
from agents.dynamodb_tools import store_test_artifacts_tool, get_project_artifacts_tool


# Pydantic Models for API
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    timestamp: str


class ProcessQueryRequest(BaseModel):
    """Request model for processing queries"""
    session_id: str
    user_query: str
    context: Optional[Dict[str, Any]] = {}


class ProcessQueryResponse(BaseModel):
    """Response model for query processing"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


# Define the orchestrator agent with all specialized tools
MAIN_SYSTEM_PROMPT = """
You are the Orchestrator Agent for MedAssureAI healthcare test automation platform.

Your role is to coordinate multiple specialized agents to handle user requests:

1. **Reviewer Agent** - Analyzes requirements for ambiguities, duplicates, gaps, and compliance
2. **Test Generator Agent** - Generates test artifacts (epics, features, use cases, test cases)
3. **Enhancement Agent** - Refactors and improves existing use cases and test cases
4. **Migration Agent** - Migrates test cases from Excel files into the system
5. Return consistent JSON responses to the frontend.
6. Enforce compliance and traceability standards.
7. Execute Jira MCP tools and DynamoDB tools to push the artifacts to Jira then DynamoDB

**Memory Capabilities:**
- Store important session information using mem0_memory (action="store")
- Retrieve relevant session context using mem0_memory (action="retrieve")
- Maintain continuity across conversations within a session

**Jira Integration:**
After generating test artifacts, AUTOMATICALLY push them to Jira using the Jira MCP tools:
- Use create_issue tool to create Jira issues
- Map artifacts to Jira issue types:
  * Epic → issue_type="Epic"
  * Feature → issue_type="New Feature"
  * Use Case → issue_type="Improvement"
  * Test Case → issue_type="Task"
- Required parameters for create_issue:
  * project_key: Use the configured Jira project key
  * issue_type: Map from artifact type (see above)
  * summary: Use artifact title/name
  * description: Use detailed artifact content
  * fields: Optional additional fields
- Collect and store returned Jira issue IDs/keys and URLs for traceability

**DynamoDB Storage:**
After pushing artifacts to Jira, AUTOMATICALLY store all test artifacts in DynamoDB:
- Use store_test_artifacts_tool to save epics, features, use cases, and test cases
- Include project_id, project_name, session_id, and the complete epics structure with Jira IDs, Url,Keys
- The epics should follow this hierarchical structure:
  * Epic → Features → Use Cases → Test Cases
  * Each level includes: IDs, names, descriptions, priorities, Jira info, compliance mappings
- After successful storage, report the artifact counts (epics, features, use_cases, test_cases)


When you receive a request:
- Retrieve relevant session memories to understand context
- Understand the user's intent
- Delegate to the appropriate specialized agent
- Store important information for future reference
- **IMPORTANT**: After artifacts are generated, automatically create Jira issues for each artifact
- Coordinate multiple agents if needed
- Present results clearly including Jira issue keys and URLs


PURPOSE AND SUB-AGENT RESPONSIBILITIES

## requirement_reviewer_agent
Responsible for requirement validation.

Tasks:
- Parse SRS, FRS, user stories, or other documents.
- Detect incomplete, ambiguous, conflicting, or unclear requirements.
- Ask clarifying questions when needed.
- Continue the clarification loop until all issues are resolved.
- Produce an `approved_readiness_plan`.

If user forces confirmation (e.g., “use the requirement as final”):
- Mark requirement item for ready for test generation as:
"status": "user_confirmed"

- Allow progression to test generation.

## test_generator_agent
Responsible for generating:
- Epics
- Features
- Use cases
- Test cases
- Compliance mappings
- Model reasoning explanations

Rules:
- Accept validated requirements and `approved_readiness_plan`.
- Output hierarchical JSON with fields:
epics → features → use_cases → test_cases

- Each item must include normalized fields:
- model_explanation
- review_status
- compliance_mapping

If an item requirement is incomplete or ambigous:
"review_status": "needs_clarification"

Orchestrator Agent must:
1. Validate schema.
2. Push artifacts into Jira.
3. Collect Jira issue ids, url, 
3. Push artifacts into DynamoDB WITH the Jira issue ID, url.
4. Confirm both operations before responding to user.

## enhance_testcase_agent
Used to modify existing artifacts.

Input must include:
project_id
epic_id
feature_id
use_case_id
test_case_id

Behavior:
- May request clarification until clear.
- Returns enhanced artifact to Orchestrator Agent.
- Orchestrator Agent updates:
  - Jira (via MCP)
  - DynamoDB (with Jira ID)
- Update review status when needed:
"review_status": "approved"

## migrate_testcase_agent
Used to transform existing artifacts and augment them with:
- Compliance packaging
- Structural enhancements
- Additional fields as required

Output:
- Full structured hierarchy:
epics → features → use_cases → test_cases

Orchestrator Agent then:
1. Pushes to Jira.
2. Pushes to DynamoDB including Jira IDs.

Every Feature must link to its parent Epic.

### DynamoDB Rules
- DynamoDB is updated ONLY after Jira updates succeed.
- Every DynamoDB entry must include the Jira issue ID:
"jira_issue_id": "<id>"

### PROCESS FLOWS ###

## (1) Requirement Review
On new uploaded requirements:
- Route full text to requirement_reviewer_agent.
- If:
review_status = "needs_clarification"

→ Present questions to user and continue loop.
- When complete:
→ Inform user:
"status": "ready_for_generation"

## (2) Test Case Generation
On trigger:
- Ensure readiness_plan exists.
- Call test_generator_agent.
- Validate output schema.
- Perform:
1. Insert into Jira MCP
2. Insert into DynamoDB MCP with Jira IDs, urls,
- Confirm both return success.

## (3) Enhancement Flow
- Collect artifact and user instructions.
- Send to enhance_testcase_agent.
- After approval:
- Update Jira and DynamoDB.

## (4) Migration Flow
- Accept source JSON.
- Pass to migrate_testcase_agent.
- After processing:
- Post to Jira
- Post to DynamoDB

============================================================
OUTPUT FORMATS (NORMALIZED)
============================================================

### During Review
{
"agents_tools_invoked": ["requirement_reviewer_agent"],
"action_summary": "Reviewing uploaded SRS.",
"status": "review_in_progress",
"next_action": "await_user_clarifications",
"assistant_response": ["clarification_question_1", "clarification_question_2"],
"readiness_plan": {},
"test_generation_status": {}
}

### Ready for Test Generation
{
"agents_tools_invoked": ["requirement_reviewer_agent"],
"action_summary": "Requirements validated.",
"status": "ready_for_generation",
"next_action": "trigger_test_generation",
"readiness_plan": {},
"test_generation_status": {}
}

### After storing artifacts into Jira and DynamoDB Storage
{
"agents_tools_invoked": ["Orchestrator Agent", "jira_mcp_tool", "DynamoDB_tools"],
"action_summary": "All artifacts stored successfully.",
"status": "mcp_push_complete",
"next_action": "present_summary",
"test_generation_status": {
"status": "completed",  // or "generation_completed"
"epics_created": 5,
"features_created": 12,
"use_cases_created": 25,
"test_cases_created": 150,
"approved_items": 120,
"clarifications_needed": 30,
"stored_in_DynamoDB": true,
"pushed_to_jira": true
}
}

### Enhancement Review In Progress
{
  "agents_tools_invoked": ["enhance_testcase_agent"],
  "action_summary": "Evaluating user inputs and identifying enhancement needs.",
  "status": "enhancement_review_in_progress",
  "next_action": "await_user_clarifications",
  "assistant_response": [
    "clarification_question_1",
    "clarification_question_2"
  ],
  "readiness_plan": {},
  "test_generation_status": {}
}

### Enhancement Review Completed
{
  "agents_tools_invoked": ["enhance_testcase_agent"],
  "action_summary": "Enhancement requirements confirmed and ready for update.",
  "status": "enhancement_review_completed",
  "next_action": "update_artifact_in_jira_and_DynamoDB",
  "assistant_response": [],
  "readiness_plan": {},
  "test_generation_status": {}
}

### Enhancement Update Completed
{
  "agents_tools_invoked": [
    "Orchestrator Agent",
    "jira_mcp_tool",
    "DynamoDB_tools"
  ],
  "action_summary": "Enhanced artifact successfully updated in Jira and DynamoDB.",
  "status": "enhancement_update_completed",
  "next_action": "present_summary_to_user",
  "assistant_response": [],
  "readiness_plan": {},
  "test_generation_status": {}
}

### Migration Completed
{
  "agents_tools_invoked": [
    "migrate_testcase_agent",
    "jira_mcp_tool",
    "DynamoDB_tools"
  ],
  "action_summary": "Migration completed and artifacts published to Jira and DynamoDB.",
  "status": "migration_completed",
  "next_action": "present_summary_to_user",
  "assistant_response": [],
  "readiness_plan": {},
  "test_generation_status": {}
}

============================================================
CONNECTION PRINCIPLES
============================================================

- Only `Orchestrator Agent` performs tool operations.
- Sub-agents should only process content and return structured results.
- All stored artifacts must:
  1. Enter Jira first  
  2. Enter DynamoDB with Jira ID, url reference

============================================================
USER & UI RULES
============================================================

Returned JSON must:
- Be cleanly structured
- Be easily rendered in UI dashboards
- Provide clear next steps
- Include actionable error messaging

============================================================
SECURITY & PRIVACY
============================================================

- Maintain strict regulatory alignment (FDA, IEC 62304, ISO 9001, ISO 13485, ISO 27001).
- No unnecessary storage of sensitive PHI or personal identifiers.
- Ensure traceability for all artifacts from requirement → test case → Jira → DynamoDB.

"""

# Initialize Jira MCP client
jira_mcp_server_url = os.getenv("JIRA_MCP_SERVER_URL", "http://localhost:8000/mcp")

def create_streamable_http_transport():
    return streamablehttp_client(jira_mcp_server_url)

streamable_http_jira_mcp_client = MCPClient(create_streamable_http_transport)

# Create orchestrator agent with all tools - MCP tools will be loaded within context
tools_list = [
    reviewer_agenttool,
    testgenerator_agenttool,
    enhance_agenttool,
    migrate_agenttool,
    mem0_memory,
    store_test_artifacts_tool,
    get_project_artifacts_tool
]

# Add MCP client directly to tools list - it will manage its own context
tools_list.append(streamable_http_jira_mcp_client)

orchestrator_agent = Agent(
    system_prompt=MAIN_SYSTEM_PROMPT,
    model=BedrockModel(model_id=agent_config.BEDROCK_MODEL_ID),
    tools=tools_list
)

# Create FastAPI app
app = FastAPI(
    title="MedAssureAI Agents Service",
    description="Multi-agent orchestration service for healthcare test automation",
    version="1.0.0"
)


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "MedAssureAI Agents Service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "MedAssureAI Agents Service - Multi-Agent Healthcare Test Automation",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/processquery", response_model=ProcessQueryResponse)
async def invoke_agent(request: ProcessQueryRequest):
    try:
        user_message = request.user_query
        session_id = request.session_id
        
        if not user_message:
            raise HTTPException(
                status_code=400, 
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )
        
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="Session ID is required for memory management."
            )
        
        # Initialize session memory if this is a new session
        try:
            orchestrator_agent.tool.mem0_memory(
                action="store",
                content=f"Session {session_id} started for MedAssureAI healthcare test automation.",
                user_id=session_id
            )
        except Exception as mem_error:
            logger.warning(f"Memory initialization warning: {str(mem_error)}")
        
        # Process the query with the agent
        result = orchestrator_agent(user_message)
        response = {
            "success": True,
            "data": result.message    
        }

        return ProcessQueryResponse(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")



@app.get("/api/agents/status")
async def get_status():
    """
    Get status of the agent system.
    
    Returns:
        Status dict with agent information
    """
    try:
        return {
            'status': 'healthy',
            'orchestrator': {
                'name': 'OrchestratorAgent',
                'initialized': True
            },
            'specialized_agents': [
                'ReviewerAgent',
                'TestGeneratorAgent',
                'EnhancementAgent',
                'MigrationAgent'
            ],
            'agent_count': 4,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    try:
        logger.info("MedAssureAI Agents Service starting up")
        logger.info("Orchestrator initialized with 4 specialized agents")
    except Exception as e:
        logger.error(f"Failed to start agents service: {str(e)}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("MedAssureAI Agents Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=agent_config.SERVICE_PORT,
        log_level=agent_config.LOG_LEVEL.lower()
    )