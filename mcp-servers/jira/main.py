"""
Jira MCP Server
Provides Model Context Protocol tools for Jira operations using FastMCP.
"""
import threading
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from mcp.server import FastMCP

from config import config
from logger import logger
from jira_client import jira_client

# Load environment variables
load_dotenv()

# Create an MCP server
mcp = FastMCP("Jira MCP Server")


# MCP Tools
@mcp.tool(description="Create a Jira issue with specified details")
def create_issue(
    project_key: str,
    issue_type: str,
    summary: str,
    description: str,
    fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a Jira issue.
    
    Args:
        project_key: Jira project key (e.g., 'MED')
        issue_type: Issue type (e.g., 'Epic', 'Story', 'Task')
        summary: Issue summary/title
        description: Issue description
        fields: Additional custom fields (optional)
        
    Returns:
        Issue key, ID, and URL
    """
    logger.info(f"create_issue called: {project_key}/{issue_type}")
    result = jira_client.create_issue(
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description=description,
        fields=fields
    )
    return result


@mcp.tool(description="Update an existing Jira issue")
def update_issue(issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a Jira issue.
    
    Args:
        issue_key: Issue key (e.g., 'MED-123')
        fields: Fields to update as key-value pairs
        
    Returns:
        Success status
    """
    logger.info(f"update_issue called: {issue_key}")
    result = jira_client.update_issue(
        issue_key=issue_key,
        fields=fields
    )
    return result


@mcp.tool(description="Delete a Jira issue")
def delete_issue(issue_key: str) -> Dict[str, Any]:
    """
    Delete a Jira issue.
    
    Args:
        issue_key: Issue key (e.g., 'MED-123')
        
    Returns:
        Success status
    """
    logger.info(f"delete_issue called: {issue_key}")
    result = jira_client.delete_issue(issue_key)
    return result


@mcp.tool(description="Get details of a Jira issue")
def get_issue(issue_key: str) -> Dict[str, Any]:
    """
    Get a Jira issue.
    
    Args:
        issue_key: Issue key (e.g., 'MED-123')
        
    Returns:
        Issue details including summary, status, assignee, etc.
    """
    logger.info(f"get_issue called: {issue_key}")
    result = jira_client.get_issue(issue_key)
    return result


@mcp.tool(description="Search for Jira issues using JQL (Jira Query Language)")
def search_issues(
    jql_query: str,
    max_results: int = 50,
    start_at: int = 0
) -> Dict[str, Any]:
    """
    Search for Jira issues using JQL.
    
    Args:
        jql_query: JQL query string (e.g., 'project = MED AND status = Open')
        max_results: Maximum number of results to return (default: 50)
        start_at: Starting index for pagination (default: 0)
        
    Returns:
        List of matching issues with their details
    """
    logger.info(f"search_issues called: {jql_query}")
    result = jira_client.search_issues(
        jql_query=jql_query,
        max_results=max_results,
        start_at=start_at
    )
    return result


@mcp.tool(description="Create multiple Jira issues in batch operation")
async def create_issues_batch(
    jira_issues: List[Dict[str, Any]],
    project_key: str
) -> Dict[str, Any]:
    """
    Create multiple Jira issues in batch.
    
    Args:
        jira_issues: List of issue dictionaries, each containing:
            - summary: Issue title/summary (required)
            - description: Issue description (required)
            - issue_type: Type of issue (e.g., 'Epic', 'Story', 'Task') (required)
            - fields: Additional custom fields (optional)
        project_key: Jira project key (e.g., 'MED', 'TEST')
        
    Returns:
        Dictionary containing lists of created and failed issues with their details
        
    Example:
        jira_issues = [
            {
                "summary": "Implement user authentication",
                "description": "Add OAuth2 authentication",
                "issue_type": "Story"
            },
            {
                "summary": "Fix login bug",
                "description": "Users cannot login with special characters",
                "issue_type": "Bug"
            }
        ]
    """
    logger.info(f"create_issues_batch called: {len(jira_issues)} issues for project {project_key}")
    result = await jira_client.create_issues_in_batch(
        jira_issues=jira_issues,
        project_key=project_key
    )
    return result


def main():
    """Run the MCP server."""
    logger.info("Starting Jira MCP Server")
    logger.info(f"Jira URL: {config.JIRA_URL}")
    logger.info(f"Client configured: {bool(jira_client.client)}")
    
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    # Run in a separate thread
    thread = threading.Thread(target=main)
    thread.start()

