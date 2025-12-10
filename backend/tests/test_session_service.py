"""
Unit tests for Session Management Service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from backend.services.session_service import SessionService


class TestSessionService:
    """Test suite for SessionService."""
    
    @pytest.fixture
    def service(self):
        """Create SessionService instance with mocked OpenSearch client."""
        with patch('backend.services.session_service.opensearch_client') as mock_client:
            mock_client.ensure_index_exists.return_value = True
            service = SessionService()
            service.opensearch_client = mock_client
            return service
    
    @pytest.fixture
    def mock_opensearch(self):
        """Mock OpenSearch client."""
        with patch('backend.services.session_service.opensearch_client') as mock:
            yield mock
    
    def test_create_session_success(self, service, mock_opensearch):
        """Test successful session creation."""
        mock_opensearch.index_document.return_value = True
        
        session_id = service.create_session(
            session_type='generation',
            project_id='test-project',
            user_id='test-user'
        )
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        
        # Verify index_document was called
        mock_opensearch.index_document.assert_called_once()
        call_args = mock_opensearch.index_document.call_args
        
        doc = call_args[1]['document']
        assert doc['session_type'] == 'generation'
        assert doc['project_id'] == 'test-project'
        assert doc['user_id'] == 'test-user'
        assert doc['status'] == 'active'
        assert 'expires_at' in doc
    
    def test_create_session_with_context(self, service, mock_opensearch):
        """Test session creation with initial context."""
        mock_opensearch.index_document.return_value = True
        
        initial_context = {'key': 'value', 'data': [1, 2, 3]}
        
        session_id = service.create_session(
            session_type='enhancement',
            project_id='test-project',
            user_id='test-user',
            initial_context=initial_context
        )
        
        call_args = mock_opensearch.index_document.call_args
        doc = call_args[1]['document']
        
        assert doc['context'] == initial_context
    
    def test_create_session_invalid_type(self, service):
        """Test session creation with invalid type."""
        with pytest.raises(ValueError, match="Invalid session type"):
            service.create_session(
                session_type='invalid_type',
                project_id='test-project',
                user_id='test-user'
            )
    
    def test_create_session_opensearch_failure(self, service, mock_opensearch):
        """Test session creation when OpenSearch fails."""
        mock_opensearch.index_document.return_value = False
        
        with pytest.raises(Exception, match="Failed to create session"):
            service.create_session(
                session_type='generation',
                project_id='test-project',
                user_id='test-user'
            )
    
    def test_append_message_success(self, service, mock_opensearch):
        """Test appending message to session."""
        # Mock get_session
        mock_session = {
            'session_id': 'test-session',
            'messages': [],
            'status': 'active',
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        mock_opensearch.get_document.return_value = mock_session
        mock_opensearch.update_document.return_value = True
        
        success = service.append_message(
            session_id='test-session',
            role='user',
            content='Test message'
        )
        
        assert success is True
        
        # Verify update was called
        mock_opensearch.update_document.assert_called_once()
        call_args = mock_opensearch.update_document.call_args
        
        updates = call_args[1]['updates']
        assert len(updates['messages']) == 1
        assert updates['messages'][0]['role'] == 'user'
        assert updates['messages'][0]['content'] == 'Test message'
    
    def test_append_message_session_not_found(self, service, mock_opensearch):
        """Test appending message to non-existent session."""
        mock_opensearch.get_document.return_value = None
        
        with pytest.raises(ValueError, match="Session not found"):
            service.append_message(
                session_id='nonexistent',
                role='user',
                content='Test'
            )
    
    def test_append_message_expired_session(self, service, mock_opensearch):
        """Test appending message to expired session."""
        mock_session = {
            'session_id': 'test-session',
            'messages': [],
            'status': 'active',
            'expires_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        mock_opensearch.get_document.return_value = mock_session
        
        with pytest.raises(ValueError, match="Session expired"):
            service.append_message(
                session_id='test-session',
                role='user',
                content='Test'
            )
    
    def test_get_session_success(self, service, mock_opensearch):
        """Test retrieving session."""
        mock_session = {
            'session_id': 'test-session',
            'session_type': 'generation',
            'status': 'active'
        }
        mock_opensearch.get_document.return_value = mock_session
        
        session = service.get_session('test-session')
        
        assert session is not None
        assert session['session_id'] == 'test-session'
        assert session['session_type'] == 'generation'
    
    def test_get_session_not_found(self, service, mock_opensearch):
        """Test retrieving non-existent session."""
        mock_opensearch.get_document.return_value = None
        
        session = service.get_session('nonexistent')
        
        assert session is None
    
    def test_update_context_success(self, service, mock_opensearch):
        """Test updating session context."""
        mock_session = {
            'session_id': 'test-session',
            'context': {'existing': 'value'}
        }
        mock_opensearch.get_document.return_value = mock_session
        mock_opensearch.update_document.return_value = True
        
        success = service.update_context(
            session_id='test-session',
            context_updates={'new_key': 'new_value'}
        )
        
        assert success is True
        
        # Verify update was called with merged context
        call_args = mock_opensearch.update_document.call_args
        updates = call_args[1]['updates']
        
        assert updates['context']['existing'] == 'value'
        assert updates['context']['new_key'] == 'new_value'
    
    def test_update_status_success(self, service, mock_opensearch):
        """Test updating session status."""
        mock_opensearch.update_document.return_value = True
        
        success = service.update_status(
            session_id='test-session',
            status='complete'
        )
        
        assert success is True
        
        call_args = mock_opensearch.update_document.call_args
        updates = call_args[1]['updates']
        assert updates['status'] == 'complete'
    
    def test_update_status_invalid(self, service):
        """Test updating with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            service.update_status(
                session_id='test-session',
                status='invalid_status'
            )
    
    def test_get_messages(self, service, mock_opensearch):
        """Test retrieving session messages."""
        mock_session = {
            'session_id': 'test-session',
            'messages': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'agent', 'content': 'Hi there'}
            ]
        }
        mock_opensearch.get_document.return_value = mock_session
        
        messages = service.get_messages('test-session')
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[1]['role'] == 'agent'
    
    def test_get_context(self, service, mock_opensearch):
        """Test retrieving session context."""
        mock_session = {
            'session_id': 'test-session',
            'context': {'key1': 'value1', 'key2': 'value2'}
        }
        mock_opensearch.get_document.return_value = mock_session
        
        context = service.get_context('test-session')
        
        assert context['key1'] == 'value1'
        assert context['key2'] == 'value2'
    
    def test_delete_session(self, service, mock_opensearch):
        """Test deleting session."""
        mock_opensearch.delete_document.return_value = True
        
        success = service.delete_session('test-session')
        
        assert success is True
        mock_opensearch.delete_document.assert_called_once_with(doc_id='test-session')
    
    def test_get_sessions_by_project(self, service, mock_opensearch):
        """Test retrieving sessions by project."""
        mock_sessions = [
            {'session_id': 'session-1', 'project_id': 'project-1'},
            {'session_id': 'session-2', 'project_id': 'project-1'}
        ]
        mock_opensearch.search.return_value = mock_sessions
        
        sessions = service.get_sessions_by_project('project-1')
        
        assert len(sessions) == 2
        assert all(s['project_id'] == 'project-1' for s in sessions)
    
    def test_get_sessions_by_user(self, service, mock_opensearch):
        """Test retrieving sessions by user."""
        mock_sessions = [
            {'session_id': 'session-1', 'user_id': 'user-1'},
            {'session_id': 'session-2', 'user_id': 'user-1'}
        ]
        mock_opensearch.search.return_value = mock_sessions
        
        sessions = service.get_sessions_by_user('user-1')
        
        assert len(sessions) == 2
        assert all(s['user_id'] == 'user-1' for s in sessions)
    
    def test_cleanup_expired_sessions(self, service, mock_opensearch):
        """Test cleaning up expired sessions."""
        expired_sessions = [
            {'session_id': 'expired-1'},
            {'session_id': 'expired-2'}
        ]
        mock_opensearch.search.return_value = expired_sessions
        mock_opensearch.update_document.return_value = True
        
        count = service.cleanup_expired_sessions()
        
        assert count == 2
        assert mock_opensearch.update_document.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
