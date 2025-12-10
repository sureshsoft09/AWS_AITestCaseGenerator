"""
Client for communicating with the agents service.
Backend uses this to call agents via HTTP instead of direct import.
"""
import httpx
from typing import Dict, Any, Optional
from backend.config import config
from backend.logger import logger


class AgentClient:
    """Client for agents service HTTP API."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize agent client.
        
        Args:
            base_url: Base URL of agents service (defaults to config)
        """
        self.base_url = base_url or "http://localhost:8001"
        self.timeout = 300.0  # 5 minutes for long-running agent operations
        
    async def process_request(
        self,
        session_id: str,
        user_query: str,
        load_session_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user request through the agents service.
        
        Args:
            session_id: Session identifier
            user_query: User's query or message
            load_session_context: Whether to load session context
            
        Returns:
            Response dict with structure:
            {
                'success': bool,
                'data': {
                    'answer': str,
                    'response': str
                },
                'error': Optional[str],
                'metadata': dict
            }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/agents/process",
                    json={
                        "session_id": session_id,
                        "user_query": user_query,
                        "load_session_context": load_session_context
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(
                    "Agent request processed",
                    extra={
                        'session_id': session_id,
                        'success': result.get('success')
                    }
                )
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(
                "Agent service HTTP error",
                extra={
                    'session_id': session_id,
                    'error': str(e)
                }
            )
            return {
                'success': False,
                'data': {
                    'answer': '',
                    'response': ''
                },
                'error': f"Agent service error: {str(e)}",
                'metadata': {}
            }
        except Exception as e:
            logger.error(
                "Agent client error",
                extra={
                    'session_id': session_id,
                    'error': str(e)
                }
            )
            return {
                'success': False,
                'data': {
                    'answer': '',
                    'response': ''
                },
                'error': f"Failed to communicate with agents: {str(e)}",
                'metadata': {}
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of the agent system.
        
        Returns:
            Status dict with agent information
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/agents/status"
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get agent status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def health_check(self) -> bool:
        """
        Check if agents service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/health"
                )
                
                return response.status_code == 200
                
        except Exception:
            return False


# Create singleton instance
agent_client = AgentClient()
