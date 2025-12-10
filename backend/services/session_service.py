"""
Session Management Service for MedAssureAI.
Handles agent session creation, updates, and retrieval using OpenSearch.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.services.opensearch_client import opensearch_client
from backend.logger import logger


class SessionService:
    """Service for managing agent sessions."""
    
    # Session types
    SESSION_TYPE_GENERATION = 'generation'
    SESSION_TYPE_ENHANCEMENT = 'enhancement'
    SESSION_TYPE_MIGRATION = 'migration'
    
    # Session statuses
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETE = 'complete'
    STATUS_EXPIRED = 'expired'
    STATUS_ERROR = 'error'
    
    # Default session TTL: 24 hours
    DEFAULT_TTL_HOURS = 24
    
    def __init__(self):
        """Initialize session service."""
        # Ensure OpenSearch index exists
        opensearch_client.ensure_index_exists()
    
    def create_session(
        self,
        session_type: str,
        project_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        initial_context: Optional[Dict] = None,
        context: Optional[Dict] = None,
        ttl_hours: Optional[int] = None
    ) -> str:
        """
        Create a new agent session.
        
        Args:
            session_type: Type of session (generation, enhancement, migration)
            project_id: Associated project ID
            user_id: User ID (optional, defaults to 'system')
            session_id: Specific session ID to use (optional, generates UUID if not provided)
            initial_context: Initial context data (optional, deprecated - use context)
            context: Initial context data (optional)
            ttl_hours: Session TTL in hours (optional, defaults to 24)
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If session type is invalid
            Exception: If session creation fails
        """
        # Validate session type
        valid_types = [
            self.SESSION_TYPE_GENERATION,
            self.SESSION_TYPE_ENHANCEMENT,
            self.SESSION_TYPE_MIGRATION
        ]
        if session_type not in valid_types:
            raise ValueError(f"Invalid session type: {session_type}")
        
        # Use provided session_id or generate new one
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Use provided user_id or default to 'system'
        if not user_id:
            user_id = 'system'
        
        # Support both initial_context and context parameters
        session_context = context or initial_context or {}
        
        # Calculate expiration
        ttl = ttl_hours or self.DEFAULT_TTL_HOURS
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl)
        
        # Create session document
        session_doc = {
            'session_id': session_id,
            'session_type': session_type,
            'project_id': project_id,
            'user_id': user_id,
            'context': session_context,
            'messages': [],
            'status': self.STATUS_ACTIVE,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'expires_at': expires_at.isoformat()
        }
        
        # Index in OpenSearch
        success = opensearch_client.index_document(
            document=session_doc,
            doc_id=session_id
        )
        
        if not success:
            raise Exception("Failed to create session in OpenSearch")
        
        logger.info(
            "Session created",
            extra={
                'session_id': session_id,
                'session_type': session_type,
                'project_id': project_id,
                'user_id': user_id
            }
        )
        
        return session_id
    
    def append_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Append a message to the session.
        
        Args:
            session_id: Session ID
            role: Message role (user, agent, system)
            content: Message content
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If session not found or expired
        """
        # Get current session
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if expired
        if self._is_expired(session):
            raise ValueError(f"Session expired: {session_id}")
        
        # Create message
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Append to messages array
        messages = session.get('messages', [])
        messages.append(message)
        
        # Update session
        updates = {
            'messages': messages,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = opensearch_client.update_document(
            doc_id=session_id,
            updates=updates
        )
        
        if not success:
            logger.error(
                "Failed to append message",
                extra={'session_id': session_id, 'role': role}
            )
            return False
        
        logger.info(
            "Message appended",
            extra={
                'session_id': session_id,
                'role': role,
                'message_count': len(messages)
            }
        )
        
        return True
    
    def get_session(self, session_id: str, max_retries: int = 5) -> Optional[Dict]:
        """
        Retrieve full session context with retry logic for eventual consistency.
        
        Args:
            session_id: Session ID
            max_retries: Maximum number of retry attempts for OpenSearch Serverless
            
        Returns:
            Session dict or None if not found
        """
        import time
        
        # Try multiple times for OpenSearch Serverless eventual consistency
        for attempt in range(max_retries):
            session = opensearch_client.get_document(doc_id=session_id)
            
            if session:
                logger.info(
                    "Session retrieved",
                    extra={
                        'session_id': session_id,
                        'status': session.get('status'),
                        'message_count': len(session.get('messages', [])),
                        'attempt': attempt + 1
                    }
                )
                return session
            
            # If not found and not last attempt, wait and retry
            if attempt < max_retries - 1:
                wait_time = 1.0 * (attempt + 1)  # Exponential backoff: 1s, 2s, 3s, 4s, 5s
                logger.info(
                    "Session not found, retrying",
                    extra={
                        'session_id': session_id,
                        'attempt': attempt + 1,
                        'wait_time': wait_time
                    }
                )
                time.sleep(wait_time)
        
        logger.warning(
            "Session not found after retries",
            extra={'session_id': session_id, 'attempts': max_retries}
        )
        return None
    
    def update_context(
        self,
        session_id: str,
        context_updates: Dict
    ) -> bool:
        """
        Update session context by merging new data.
        
        Args:
            session_id: Session ID
            context_updates: Context fields to update/merge
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If session not found
        """
        # Get current session
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Merge context
        current_context = session.get('context', {})
        current_context.update(context_updates)
        
        # Update session
        updates = {
            'context': current_context,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = opensearch_client.update_document(
            doc_id=session_id,
            updates=updates
        )
        
        if not success:
            logger.error(
                "Failed to update context",
                extra={'session_id': session_id}
            )
            return False
        
        logger.info(
            "Context updated",
            extra={
                'session_id': session_id,
                'context_keys': list(context_updates.keys())
            }
        )
        
        return True
    
    def update_status(
        self,
        session_id: str,
        status: str
    ) -> bool:
        """
        Update session status.
        
        Args:
            session_id: Session ID
            status: New status (active, complete, expired, error)
            
        Returns:
            True if successful
        """
        valid_statuses = [
            self.STATUS_ACTIVE,
            self.STATUS_COMPLETE,
            self.STATUS_EXPIRED,
            self.STATUS_ERROR
        ]
        
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        updates = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        success = opensearch_client.update_document(
            doc_id=session_id,
            updates=updates
        )
        
        if success:
            logger.info(
                "Session status updated",
                extra={'session_id': session_id, 'status': status}
            )
        
        return success
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """
        Get all messages from a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of messages
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.get('messages', [])
    
    def get_context(self, session_id: str) -> Dict:
        """
        Get session context.
        
        Args:
            session_id: Session ID
            
        Returns:
            Context dict
        """
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return session.get('context', {})
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        success = opensearch_client.delete_document(doc_id=session_id)
        
        if success:
            logger.info(
                "Session deleted",
                extra={'session_id': session_id}
            )
        
        return success
    
    def get_sessions_by_project(
        self,
        project_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get all sessions for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions
        """
        query = {
            'term': {'project_id': project_id}
        }
        
        sessions = opensearch_client.search(
            query=query,
            size=limit
        )
        
        logger.info(
            "Retrieved project sessions",
            extra={
                'project_id': project_id,
                'session_count': len(sessions)
            }
        )
        
        return sessions
    
    def get_sessions_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions
        """
        query = {
            'term': {'user_id': user_id}
        }
        
        sessions = opensearch_client.search(
            query=query,
            size=limit
        )
        
        logger.info(
            "Retrieved user sessions",
            extra={
                'user_id': user_id,
                'session_count': len(sessions)
            }
        )
        
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # Query for expired sessions
        query = {
            'range': {
                'expires_at': {
                    'lt': datetime.utcnow().isoformat()
                }
            }
        }
        
        expired_sessions = opensearch_client.search(
            query=query,
            size=100
        )
        
        cleaned_count = 0
        for session in expired_sessions:
            session_id = session.get('session_id')
            if session_id:
                # Update status to expired
                if self.update_status(session_id, self.STATUS_EXPIRED):
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(
                "Cleaned up expired sessions",
                extra={'count': cleaned_count}
            )
        
        return cleaned_count
    
    def _is_expired(self, session: Dict) -> bool:
        """
        Check if session is expired.
        
        Args:
            session: Session dict
            
        Returns:
            True if expired
        """
        expires_at_str = session.get('expires_at')
        if not expires_at_str:
            return False
        
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            return datetime.utcnow() > expires_at.replace(tzinfo=None)
        except Exception:
            return False


# Create singleton instance
session_service = SessionService()
