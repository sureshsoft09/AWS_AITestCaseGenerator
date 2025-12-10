"""
Jira MCP Server
Provides Model Context Protocol tools for Jira operations.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from config import config
from logger import logger
from jira_client import jira_client

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Jira MCP Server",
    description="Model Context Protocol server for Jira operations",
    version="1.0.0"
)


# Request/Response Models
class CreateIssueRequest(BaseModel):
    """Request model for create_issue."""
    project_key: str = Field(..., description="Jira project key (e.g., 'MED')")
    issue_type: str = Field(..., description="Issue type (e.g., 'Epic', 'Story', 'Task')")
    summary: str = Field(..., description="Issue summary/title")
    description: str = Field(..., description="Issue description")
    fields: Optional[Dict[str, Any]] = Field(None, description="Additional fields")


class UpdateIssueRequest(BaseModel):
    """Request model for update_issue."""
    issue_key: str = Field(..., description="Issue key (e.g., 'MED-123')")
    fields: Dict[str, Any] = Field(..., description="Fields to update")


class DeleteIssueRequest(BaseModel):
    """Request model for delete_issue."""
    issue_key: str = Field(..., description="Issue key (e.g., 'MED-123')")


class GetIssueRequest(BaseModel):
    """Request model for get_issue."""
    issue_key: str = Field(..., description="Issue key (e.g., 'MED-123')")


class SearchIssuesRequest(BaseModel):
    """Request model for search_issues."""
    jql_query: str = Field(..., description="JQL query string")
    max_results: int = Field(50, description="Maximum results to return")
    start_at: int = Field(0, description="Starting index for pagination")


# Health Check Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Jira MCP Server",
        "status": "running",
        "version": "1.0.0",
        "jira_url": config.JIRA_URL
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jira-mcp-server",
        "jira_url": config.JIRA_URL,
        "configured": bool(jira_client.client)
    }


# MCP Tools
@app.post("/tools/create_issue")
async def create_issue(request: CreateIssueRequest):
    """
    Create a Jira issue.
    
    Args:
        request: Issue details
        
    Returns:
        Issue key, ID, and URL
    """
    logger.info(f"create_issue called: {request.project_key}/{request.issue_type}")
    result = jira_client.create_issue(
        project_key=request.project_key,
        issue_type=request.issue_type,
        summary=request.summary,
        description=request.description,
        fields=request.fields
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/update_issue")
async def update_issue(request: UpdateIssueRequest):
    """
    Update a Jira issue.
    
    Args:
        request: Issue key and fields to update
        
    Returns:
        Success status
    """
    logger.info(f"update_issue called: {request.issue_key}")
    result = jira_client.update_issue(
        issue_key=request.issue_key,
        fields=request.fields
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/delete_issue")
async def delete_issue(request: DeleteIssueRequest):
    """
    Delete a Jira issue.
    
    Args:
        request: Issue key
        
    Returns:
        Success status
    """
    logger.info(f"delete_issue called: {request.issue_key}")
    result = jira_client.delete_issue(request.issue_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/get_issue")
async def get_issue(request: GetIssueRequest):
    """
    Get a Jira issue.
    
    Args:
        request: Issue key
        
    Returns:
        Issue details
    """
    logger.info(f"get_issue called: {request.issue_key}")
    result = jira_client.get_issue(request.issue_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/tools/search_issues")
async def search_issues(request: SearchIssuesRequest):
    """
    Search for Jira issues using JQL.
    
    Args:
        request: JQL query and pagination parameters
        
    Returns:
        List of matching issues
    """
    logger.info(f"search_issues called: {request.jql_query}")
    result = jira_client.search_issues(
        jql_query=request.jql_query,
        max_results=request.max_results,
        start_at=request.start_at
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Jira MCP Server starting up")
    logger.info(f"Jira URL: {config.JIRA_URL}")
    logger.info(f"Client configured: {bool(jira_client.client)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Jira MCP Server shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=config.HOST,
        port=config.PORT,
        log_level=config.LOG_LEVEL.lower()
    )
