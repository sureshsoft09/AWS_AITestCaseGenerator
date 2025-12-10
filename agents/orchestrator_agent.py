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
MAIN_SYSTEM_PROMPT = """You are the Orchestrator Agent for MedAssureAI healthcare test automation platform.

Your role is to coordinate multiple specialized agents to handle user requests:

1. **Reviewer Agent** - Analyzes requirements for ambiguities, duplicates, gaps, and compliance
2. **Test Generator Agent** - Generates test artifacts (epics, features, use cases, test cases)
3. **Enhancement Agent** - Refactors and improves existing use cases and test cases
4. **Migration Agent** - Migrates test cases from Excel files into the system

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

When you receive a request:
- Retrieve relevant session memories to understand context
- Understand the user's intent
- Delegate to the appropriate specialized agent
- Store important information for future reference
- **IMPORTANT**: After artifacts are generated, automatically create Jira issues for each artifact
- Coordinate multiple agents if needed
- Present results clearly including Jira issue keys and URLs

Always be professional, helpful, and focused on healthcare test automation needs."""

# Initialize Jira MCP client
jira_mcp_server_url = os.getenv("JIRA_MCP_SERVER_URL", "http://localhost:8000/mcp")

def create_streamable_http_transport():
    return streamablehttp_client(jira_mcp_server_url)

streamable_http_jira_mcp_client = MCPClient(create_streamable_http_transport)

# Create orchestrator agent with all tools - MCP tools will be loaded within context
tools_list = [reviewer_agenttool, testgenerator_agenttool, enhance_agenttool, migrate_agenttool, mem0_memory]

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