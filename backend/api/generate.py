"""
Test Generation API endpoints for MedAssureAI.
Handles requirements review and test artifact generation.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.logger import logger
from backend.services.agent_client import agent_client


router = APIRouter(prefix="/api/generate", tags=["generate"])


class ReviewRequest(BaseModel):
    """Request model for requirements review."""
    upload_id: str
    project_id: str
    project_name: str
    jira_project_key: Optional[str] = None
    notification_email: Optional[EmailStr] = None


class ReviewResponse(BaseModel):
    """Response model for requirements review."""
    session_id: str
    project_id: str
    status: str
    message: str
    analysis: Optional[dict] = None


class ChatRequest(BaseModel):
    """Request model for chat interaction."""
    session_id: str
    user_message: str


class ChatResponse(BaseModel):
    """Response model for chat interaction."""
    session_id: str
    agent_response: str
    status: str


class ExecuteRequest(BaseModel):
    """Request model for test generation execution."""
    session_id: str
    project_id: str
    approved: bool = True


class ExecuteResponse(BaseModel):
    """Response model for test generation execution."""
    session_id: str
    project_id: str
    status: str
    message: str
    generation_started: bool


class StatusResponse(BaseModel):
    """Response model for generation status."""
    session_id: str
    project_id: str
    status: str
    progress: dict
    artifact_counts: Optional[dict] = None


@router.post("/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def review_requirements(request: ReviewRequest):
    """
    Trigger requirements review by Review Agent.
    
    This endpoint:
    1. Creates a new session in OpenSearch
    2. Retrieves extracted text from uploaded documents
    3. Sends requirements to Review Agent for analysis
    4. Returns session ID for continued interaction
    
    Args:
        request: Review request with upload and project details
        
    Returns:
        Review response with session ID and initial analysis
    """
    import uuid
    from backend.services.session_service import session_service
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        logger.info(
            "Starting requirements review",
            extra={
                "session_id": session_id,
                "project_id": request.project_id,
                "upload_id": request.upload_id
            }
        )
        
        # Create session in OpenSearch
        session_service.create_session(
            session_id=session_id,
            session_type="generation",
            project_id=request.project_id,
            context={
                "upload_id": request.upload_id,
                "project_name": request.project_name,
                "jira_project_key": request.jira_project_key,
                "notification_email": request.notification_email,
                "phase": "review"
            }
        )
        
        # Retrieve extracted text from documents
        # In production, this would get text from Textract results
        requirements_text = _get_extracted_text(request.upload_id, request.project_id)
        
        # Send to Review Agent via HTTP
        review_result = await agent_client.process_request(
            session_id=session_id,
            user_query=f"Please analyze these requirements:\n\n{requirements_text}",
            load_session_context=True
        )
        
        # Store agent response in session
        session_service.append_message(
            session_id=session_id,
            role="assistant",
            content=review_result.get("data", {}).get("answer", "")
        )
        
        logger.info(
            "Requirements review completed",
            extra={"session_id": session_id, "success": review_result.get("success")}
        )
        
        return {
            "session_id": session_id,
            "project_id": request.project_id,
            "status": "review_completed" if review_result.get("success") else "review_failed",
            "message": review_result.get("data", {}).get("answer", "Review completed"),
            "analysis": review_result.get("metadata", {})
        }
        
    except Exception as e:
        logger.error(
            "Requirements review failed",
            extra={"project_id": request.project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirements review failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Continue conversation with agent for clarifications.
    
    This endpoint:
    1. Retrieves session context from OpenSearch
    2. Sends user message to appropriate agent
    3. Returns agent response
    4. Updates session with conversation
    
    Args:
        request: Chat request with session ID and user message
        
    Returns:
        Chat response with agent's reply
    """
    from backend.services.session_service import session_service
    
    try:
        logger.info(
            "Processing chat message",
            extra={"session_id": request.session_id}
        )
        
        # Get session context
        session = session_service.get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        # Store user message
        session_service.append_message(
            session_id=request.session_id,
            role="user",
            content=request.user_message
        )
        
        # Send to agents service via HTTP
        result = await agent_client.process_request(
            session_id=request.session_id,
            user_query=request.user_message,
            load_session_context=True
        )
        
        # Store agent response
        agent_response = result.get("data", {}).get("answer", "")
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=agent_response
        )
        
        logger.info(
            "Chat message processed",
            extra={"session_id": request.session_id, "success": result.get("success")}
        )
        
        return {
            "session_id": request.session_id,
            "agent_response": agent_response,
            "status": "success" if result.get("success") else "error"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Chat processing failed",
            extra={"session_id": request.session_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/execute", response_model=ExecuteResponse)
async def execute_generation(request: ExecuteRequest):
    """
    Execute test artifact generation after clarifications.
    
    This endpoint:
    1. Retrieves clarified requirements from session
    2. Triggers Test Case Generator Agent
    3. Generates epics, features, use cases, test cases
    4. Creates Jira issues via MCP Server
    5. Stores artifacts in DynamoDB via MCP Server
    6. Sends completion notification
    
    Args:
        request: Execute request with session ID and approval
        
    Returns:
        Execute response with generation status
    """
    from backend.services.session_service import session_service
    
    try:
        logger.info(
            "Starting test generation",
            extra={"session_id": request.session_id, "project_id": request.project_id}
        )
        
        if not request.approved:
            return {
                "session_id": request.session_id,
                "project_id": request.project_id,
                "status": "cancelled",
                "message": "Generation cancelled by user",
                "generation_started": False
            }
        
        # Get session context
        session = session_service.get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        # Update session phase
        session_service.update_context(
            session_id=request.session_id,
            context_updates={"phase": "generation", "status": "generating"}
        )
        
        # Get clarified requirements from session messages
        requirements_text = _extract_requirements_from_session(session)
        
        # Trigger Test Generator Agent
        generation_result = test_generator_agent.run(
            user_input=f"Generate test artifacts from these requirements:\n\n{requirements_text}",
            context={
                "session_id": request.session_id,
                "project_id": request.project_id,
                **session.get("context", {})
            }
        )
        
        # Store generation result
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=generation_result.get("answer", "")
        )
        
        # Update session status
        session_service.update_context(
            session_id=request.session_id,
            context_updates={"status": "completed", "generation_completed": True}
        )
        
        # Send completion notification if email provided
        context = session.get("context", {})
        notification_email = context.get("notification_email")
        
        if notification_email and generation_result.get("success"):
            from backend.services.notification_service import notification_service
            
            # Get artifact counts
            artifact_counts = _get_artifact_counts(request.project_id)
            
            # Send notification (non-blocking - errors are logged but don't fail the request)
            notification_service.send_completion_notification(
                email=notification_email,
                project_name=context.get("project_name", "Unknown Project"),
                artifact_counts=artifact_counts,
                project_id=request.project_id,
                jira_project_key=context.get("jira_project_key")
            )
        
        logger.info(
            "Test generation completed",
            extra={"session_id": request.session_id, "success": generation_result.get("success")}
        )
        
        return {
            "session_id": request.session_id,
            "project_id": request.project_id,
            "status": "generation_completed" if generation_result.get("success") else "generation_failed",
            "message": generation_result.get("answer", "Generation completed"),
            "generation_started": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Test generation failed",
            extra={"session_id": request.session_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_generation_status(session_id: str):
    """
    Get generation progress and artifact counts.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Status response with progress and artifact counts
    """
    from backend.services.session_service import session_service
    
    try:
        # Get session
        session = session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        context = session.get("context", {})
        project_id = context.get("project_id", "unknown")
        status_value = context.get("status", "unknown")
        phase = context.get("phase", "review")
        
        # Build progress information
        progress = {
            "phase": phase,
            "status": status_value,
            "messages_count": len(session.get("messages", [])),
            "generation_completed": context.get("generation_completed", False)
        }
        
        # Get artifact counts if generation completed
        artifact_counts = None
        if context.get("generation_completed"):
            artifact_counts = _get_artifact_counts(project_id)
        
        return {
            "session_id": session_id,
            "project_id": project_id,
            "status": status_value,
            "progress": progress,
            "artifact_counts": artifact_counts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get generation status",
            extra={"session_id": session_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation status: {str(e)}"
        )


def _get_extracted_text(upload_id: str, project_id: str) -> str:
    """
    Get extracted text from uploaded documents.
    
    In production, this would retrieve Textract results from S3 or database.
    For now, returns sample text.
    """
    # Simulate extracted text
    return """
    Sample Requirements Document
    
    1. The system shall authenticate users with username and password.
    2. The system shall validate user credentials against the database.
    3. The system shall display error message for invalid credentials.
    4. The system shall log all authentication attempts.
    5. The system shall comply with HIPAA security requirements.
    """


def _extract_requirements_from_session(session: dict) -> str:
    """
    Extract clarified requirements from session messages.
    """
    messages = session.get("messages", [])
    
    # Combine all user and assistant messages
    requirements_parts = []
    for msg in messages:
        if msg.get("role") in ["user", "assistant"]:
            requirements_parts.append(msg.get("content", ""))
    
    return "\n\n".join(requirements_parts)


def _get_artifact_counts(project_id: str) -> dict:
    """
    Get artifact counts for a project from DynamoDB.
    
    In production, this would query DynamoDB for actual counts.
    """
    # Simulate artifact counts
    return {
        "epics": 3,
        "features": 8,
        "use_cases": 15,
        "test_cases": 45,
        "total": 71
    }
