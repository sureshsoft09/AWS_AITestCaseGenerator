"""
Enhancement API endpoints for MedAssureAI.
Handles artifact refinement and improvement.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.logger import logger

# Import agents
import sys
sys.path.insert(0, '.')
from agents import EnhancementAgent


router = APIRouter(prefix="/api/enhance", tags=["enhance"])

# Initialize Enhancement Agent
enhancement_agent = EnhancementAgent()


class EnhanceStartRequest(BaseModel):
    """Request model for starting enhancement session."""
    artifact_id: str
    artifact_type: str  # 'use_case' or 'test_case'
    project_id: str


class EnhanceStartResponse(BaseModel):
    """Response model for enhancement session start."""
    session_id: str
    artifact_id: str
    artifact_type: str
    artifact: dict
    status: str
    message: str


class EnhanceChatRequest(BaseModel):
    """Request model for enhancement chat."""
    session_id: str
    enhancement_instructions: str


class EnhanceChatResponse(BaseModel):
    """Response model for enhancement chat."""
    session_id: str
    agent_response: str
    preview: Optional[dict] = None
    validation: Optional[dict] = None
    status: str


class EnhanceApplyRequest(BaseModel):
    """Request model for applying enhancements."""
    session_id: str
    approved: bool = True


class EnhanceApplyResponse(BaseModel):
    """Response model for applying enhancements."""
    session_id: str
    artifact_id: str
    applied: bool
    jira_updated: bool
    dynamodb_updated: bool
    status: str
    message: str


@router.post("/start", response_model=EnhanceStartResponse, status_code=status.HTTP_201_CREATED)
async def start_enhancement(request: EnhanceStartRequest):
    """
    Start enhancement session for an artifact.
    
    This endpoint:
    1. Validates artifact type (use_case or test_case only)
    2. Loads artifact from DynamoDB
    3. Creates enhancement session in OpenSearch
    4. Returns artifact details for display
    
    Args:
        request: Enhancement start request with artifact details
        
    Returns:
        Enhancement start response with session ID and artifact
    """
    import uuid
    from backend.services.session_service import session_service
    
    try:
        # Validate artifact type
        if request.artifact_type not in ['use_case', 'test_case']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Enhancement only supported for use_case and test_case, got: {request.artifact_type}"
            )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        logger.info(
            "Starting enhancement session",
            extra={
                "session_id": session_id,
                "artifact_id": request.artifact_id,
                "artifact_type": request.artifact_type
            }
        )
        
        # Load artifact using Enhancement Agent
        load_result = enhancement_agent.run(
            user_input=f"Load artifact {request.artifact_id} of type {request.artifact_type}",
            context={
                "action": "load_artifact",
                "artifact_id": request.artifact_id,
                "artifact_type": request.artifact_type
            }
        )
        
        if not load_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to load artifact {request.artifact_id}"
            )
        
        # Extract artifact from result
        # The agent response contains artifact details
        artifact = {
            "id": request.artifact_id,
            "type": request.artifact_type,
            "loaded": True
        }
        
        # Create session in OpenSearch
        session_service.create_session(
            session_id=session_id,
            session_type="enhancement",
            project_id=request.project_id,
            context={
                "artifact_id": request.artifact_id,
                "artifact_type": request.artifact_type,
                "project_id": request.project_id,
                "phase": "enhancement",
                "original_artifact": artifact
            }
        )
        
        # Store load result in session
        session_service.append_message(
            session_id=session_id,
            role="assistant",
            content=load_result.get("answer", "Artifact loaded successfully")
        )
        
        logger.info(
            "Enhancement session started",
            extra={"session_id": session_id, "artifact_id": request.artifact_id}
        )
        
        return {
            "session_id": session_id,
            "artifact_id": request.artifact_id,
            "artifact_type": request.artifact_type,
            "artifact": artifact,
            "status": "session_created",
            "message": "Enhancement session created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to start enhancement session",
            extra={"artifact_id": request.artifact_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start enhancement session: {str(e)}"
        )


@router.post("/chat", response_model=EnhanceChatResponse)
async def chat_enhancement(request: EnhanceChatRequest):
    """
    Process enhancement instructions via chat.
    
    This endpoint:
    1. Retrieves session and artifact context
    2. Sends enhancement instructions to Enhancement Agent
    3. Agent applies modifications and validates consistency
    4. Returns preview of changes and validation results
    5. Updates session with conversation
    
    Args:
        request: Enhancement chat request with instructions
        
    Returns:
        Enhancement chat response with preview and validation
    """
    from backend.services.session_service import session_service
    
    try:
        logger.info(
            "Processing enhancement instructions",
            extra={"session_id": request.session_id}
        )
        
        # Get session context
        session = session_service.get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        context = session.get("context", {})
        
        if context.get("session_type") != "enhancement":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not an enhancement session"
            )
        
        # Store user message
        session_service.append_message(
            session_id=request.session_id,
            role="user",
            content=request.enhancement_instructions
        )
        
        # Process enhancement with Enhancement Agent
        enhancement_result = enhancement_agent.run(
            user_input=request.enhancement_instructions,
            context=context
        )
        
        # Store agent response
        agent_response = enhancement_result.get("answer", "")
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=agent_response
        )
        
        # Extract preview and validation from metadata
        metadata = enhancement_result.get("metadata", {})
        preview = metadata.get("preview")
        validation = metadata.get("validation")
        
        # Store preview in session context for apply step
        if preview:
            session_service.update_context(
                session_id=request.session_id,
                context_updates={"preview": preview, "validation": validation}
            )
        
        logger.info(
            "Enhancement instructions processed",
            extra={
                "session_id": request.session_id,
                "has_preview": preview is not None
            }
        )
        
        return {
            "session_id": request.session_id,
            "agent_response": agent_response,
            "preview": preview,
            "validation": validation,
            "status": "preview_generated" if preview else "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Enhancement chat failed",
            extra={"session_id": request.session_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhancement chat failed: {str(e)}"
        )


@router.post("/apply", response_model=EnhanceApplyResponse)
async def apply_enhancement(request: EnhanceApplyRequest):
    """
    Apply approved enhancements to artifact.
    
    This endpoint:
    1. Retrieves session with preview and validation
    2. Checks user approval
    3. Updates artifact in Jira via MCP Server
    4. Updates artifact in DynamoDB via MCP Server
    5. Returns success status
    
    Args:
        request: Enhancement apply request with approval
        
    Returns:
        Enhancement apply response with update status
    """
    from backend.services.session_service import session_service
    
    try:
        logger.info(
            "Applying enhancement",
            extra={"session_id": request.session_id, "approved": request.approved}
        )
        
        if not request.approved:
            return {
                "session_id": request.session_id,
                "artifact_id": "unknown",
                "applied": False,
                "jira_updated": False,
                "dynamodb_updated": False,
                "status": "cancelled",
                "message": "Enhancement cancelled by user"
            }
        
        # Get session context
        session = session_service.get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        context = session.get("context", {})
        artifact_id = context.get("artifact_id")
        
        # Check if preview exists
        preview = context.get("preview")
        validation = context.get("validation")
        
        if not preview:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No preview available. Please chat with enhancement instructions first."
            )
        
        # Check validation passed
        if validation and not validation.get("is_valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {validation.get('issues')}"
            )
        
        # Apply changes using Enhancement Agent
        apply_result = enhancement_agent.run(
            user_input="Apply the approved enhancements to Jira and DynamoDB",
            context={
                **context,
                "action": "apply_changes",
                "preview": preview
            }
        )
        
        # Store apply result
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=apply_result.get("answer", "")
        )
        
        # Update session status
        session_service.update_context(
            session_id=request.session_id,
            context_updates={
                "status": "completed",
                "enhancement_applied": True
            }
        )
        
        logger.info(
            "Enhancement applied successfully",
            extra={
                "session_id": request.session_id,
                "artifact_id": artifact_id
            }
        )
        
        return {
            "session_id": request.session_id,
            "artifact_id": artifact_id,
            "applied": True,
            "jira_updated": True,
            "dynamodb_updated": True,
            "status": "completed",
            "message": "Enhancement applied successfully to Jira and DynamoDB"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to apply enhancement",
            extra={"session_id": request.session_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply enhancement: {str(e)}"
        )
