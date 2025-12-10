"""
Jira client with retry logic and error handling.
"""
import time
import asyncio
from jira import JIRA
from jira.exceptions import JIRAError
from typing import Dict, List, Any, Optional
from config import config
from logger import logger


class JiraClient:
    """Jira client wrapper with retry logic and error handling."""
    
    def __init__(self):
        """Initialize Jira client."""
        if not config.JIRA_URL or not config.JIRA_API_TOKEN or not config.JIRA_EMAIL:
            logger.warning("Jira credentials not fully configured")
            self.client = None
        else:
            try:
                self.client = JIRA(
                    server=config.JIRA_URL,
                    basic_auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
                )
                logger.info(f"Jira client initialized for: {config.JIRA_URL}")
            except JIRAError as e:
                logger.error(f"Failed to initialize Jira client: {str(e)}")
                self.client = None
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        for attempt in range(config.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except JIRAError as e:
                if e.status_code == 429:  # Rate limiting
                    if attempt < config.MAX_RETRIES - 1:
                        wait_time = config.RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{config.MAX_RETRIES})")
                        time.sleep(wait_time)
                    else:
                        raise
                else:
                    raise
    
    def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Jira issue.
        
        Args:
            project_key: Jira project key (e.g., "MED")
            issue_type: Issue type (e.g., "Epic", "Story", "Task")
            summary: Issue summary/title
            description: Issue description
            fields: Additional fields (optional)
            
        Returns:
            Issue details including key, ID, and URL
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            issue_dict = {
                'project': {'key': project_key},
                'issuetype': {'name': issue_type},
                'summary': summary,
                'description': description
            }
            
            # Add additional fields if provided
            if fields:
                issue_dict.update(fields)
            
            def _create():
                return self.client.create_issue(fields=issue_dict)
            
            issue = self._retry_with_backoff(_create)
            
            result = {
                "success": True,
                "issue_key": issue.key,
                "issue_id": issue.id,
                "issue_url": f"{config.JIRA_URL}/browse/{issue.key}"
            }
            
            logger.info(f"Issue created: {issue.key}")
            return result
            
        except JIRAError as e:
            error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error creating issue: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., "MED-123")
            fields: Fields to update
            
        Returns:
            Success status
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            def _update():
                issue = self.client.issue(issue_key)
                issue.update(fields=fields)
                return issue
            
            issue = self._retry_with_backoff(_update)
            
            logger.info(f"Issue updated: {issue_key}")
            return {
                "success": True,
                "issue_key": issue.key,
                "issue_id": issue.id,
                "issue_url": f"{config.JIRA_URL}/browse/{issue.key}"
            }
            
        except JIRAError as e:
            error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error updating issue: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def delete_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Delete a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., "MED-123")
            
        Returns:
            Success status
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            def _delete():
                issue = self.client.issue(issue_key)
                issue.delete()
            
            self._retry_with_backoff(_delete)
            
            logger.info(f"Issue deleted: {issue_key}")
            return {"success": True, "issue_key": issue_key}
            
        except JIRAError as e:
            error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error deleting issue: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., "MED-123")
            
        Returns:
            Issue details
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            def _get():
                return self.client.issue(issue_key)
            
            issue = self._retry_with_backoff(_get)
            
            result = {
                "success": True,
                "issue_key": issue.key,
                "issue_id": issue.id,
                "issue_url": f"{config.JIRA_URL}/browse/{issue.key}",
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "issue_type": issue.fields.issuetype.name,
                "project": issue.fields.project.key
            }
            
            logger.info(f"Issue retrieved: {issue_key}")
            return result
            
        except JIRAError as e:
            error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error getting issue: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def search_issues(
        self,
        jql_query: str,
        max_results: int = 50,
        start_at: int = 0
    ) -> Dict[str, Any]:
        """
        Search for Jira issues using JQL.
        
        Args:
            jql_query: JQL query string
            max_results: Maximum results to return
            start_at: Starting index for pagination
            
        Returns:
            List of issues matching the query
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        try:
            def _search():
                return self.client.search_issues(
                    jql_query,
                    maxResults=max_results,
                    startAt=start_at
                )
            
            issues = self._retry_with_backoff(_search)
            
            results = []
            for issue in issues:
                results.append({
                    "issue_key": issue.key,
                    "issue_id": issue.id,
                    "issue_url": f"{config.JIRA_URL}/browse/{issue.key}",
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "issue_type": issue.fields.issuetype.name
                })
            
            logger.info(f"Search completed: {len(results)} issues found")
            return {
                "success": True,
                "issues": results,
                "total": len(results)
            }
            
        except JIRAError as e:
            error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error searching issues: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def create_issues_in_batch(
        self,
        jira_issues: List[Dict[str, Any]],
        project_key: str
    ) -> Dict[str, Any]:
        """
        Create multiple Jira issues in batch.
        
        Args:
            jira_issues: List of issue dictionaries containing summary, description, and issue_type
            project_key: Jira project key (e.g., "MED")
            
        Returns:
            Dictionary with created and failed issues
        """
        if not self.client:
            return {"success": False, "error": "Jira client not initialized"}
        
        created = []
        failed = []
        
        for idx, issue in enumerate(jira_issues):
            try:
                payload = {
                    "project": {"key": project_key},
                    "summary": issue.get("summary", ""),
                    "description": issue.get("description", ""),
                    "issuetype": {"name": issue.get("issue_type", "Task")}
                }
                
                # Add any additional fields if provided
                if "fields" in issue:
                    payload.update(issue["fields"])
                
                def _create():
                    return self.client.create_issue(fields=payload)
                
                result = self._retry_with_backoff(_create)
                
                created.append({
                    "index": idx,
                    "jira_issue_id": result.id,
                    "jira_issue_key": result.key,
                    "jira_issue_url": f"{config.JIRA_URL}/browse/{result.key}",
                    "summary": issue.get("summary", "")
                })
                
                logger.info(f"Batch issue created: {result.key}")
                
            except JIRAError as e:
                error_msg = f"Jira API error: {e.text if hasattr(e, 'text') else str(e)}"
                logger.error(f"Failed to create issue at index {idx}: {error_msg}")
                failed.append({
                    "index": idx,
                    "error": error_msg,
                    "summary": issue.get("summary", "")
                })
                await asyncio.sleep(2)  # Retry spacing to avoid 429 throttling
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Failed to create issue at index {idx}: {error_msg}")
                failed.append({
                    "index": idx,
                    "error": error_msg,
                    "summary": issue.get("summary", "")
                })
                await asyncio.sleep(2)
        
        logger.info(f"Batch creation completed: {len(created)} created, {len(failed)} failed")
        return {
            "success": True,
            "created": created,
            "failed": failed,
            "total_created": len(created),
            "total_failed": len(failed)
        }


# Singleton instance
jira_client = JiraClient()
