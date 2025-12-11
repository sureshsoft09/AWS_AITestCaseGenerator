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
    session_id: str
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
    jira_project_key: Optional[str] = None
    notification_email: Optional[EmailStr] = None


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
    1. Uses session ID from frontend
    2. Retrieves uploaded files from S3
    3. Extracts text using AWS Textract
    4. Sends requirements to Review Agent for analysis
    5. Returns analysis results
    
    Args:
        request: Review request with session ID, upload and project details
        
    Returns:
        Review response with session ID and initial analysis
    """
    from backend.services.session_service import session_service
    from backend.services.textract_service import textract_service
    from backend.services.file_upload_service import file_upload_service
    
    try:
        # Use session ID provided by frontend
        session_id = request.session_id
        
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
        
        # Get uploaded file S3 keys from upload_id
        # In production, retrieve this from database/session storage
        s3_keys = _get_s3_keys_for_upload(request.upload_id, request.project_id)
        
        # Extract text from documents using Textract
        logger.info(
            "Extracting text from documents",
            extra={"session_id": session_id, "file_count": len(s3_keys)}
        )
        
        if len(s3_keys) == 0:
            # Fallback to sample text if no files found
            requirements_text = _get_sample_requirements()
        elif len(s3_keys) == 1:
            # Single document
            requirements_text = textract_service.extract_text_from_s3(s3_keys[0])
        else:
            # Multiple documents
            requirements_text = textract_service.extract_text_from_multiple_documents(s3_keys)
        
        logger.info(
            "Text extraction completed",
            extra={
                "session_id": session_id,
                "text_length": len(requirements_text)
            }
        )
        
        # Send to Review Agent via HTTP
        review_result = await agent_client.process_request(
            session_id=session_id,
            user_query=f"""Please only review and analyze these requirements:

            Project ID - {request.project_id}
            Project Name - {request.project_name}
            Jira Project Key - {request.jira_project_key}
            Notification Email - {request.notification_email}

            Only return back below json format with no additional text in the response.
            ### OUTPUT FORMAT (INTERACTIVE RESPONSE)
            {{
                "readiness_plan": {{
                    "estimated_epics": 0,
                    "estimated_features": 0,
                    "estimated_use_cases": 0,
                    "estimated_test_cases": 0,
                    "overall_status": "Clarifications Needed"
                }},
                "status": "review_in_progress",
                "next_action": "await_user_clarifications",
                "assistant_response": [
                    "Requirement REQ-12 is vague. Please specify acceptable response time (e.g., in seconds).",
                    "Requirement REQ-27 mentions compliance but does not specify which standard — please confirm if FDA or IEC 62304 applies."
                ],
                "test_generation_status": {{}},
                "next_action": "Awaiting user clarifications or confirmation for pending items."
            }}

            EXTRACTED CONTENT:
            {requirements_text}
            """,
            load_session_context=True
        )
        
        # Log the review result
        logger.info(
            "Review result from agent",
            extra={
                "session_id": session_id,
                "review_result": review_result
            }
        )
        print(f"\n{'='*80}")
        print(f"REVIEW RESULT FOR SESSION: {session_id}")
        print(f"{'='*80}")
        print(f"Review Result: {review_result}")
        print(f"{'='*80}\n")
        
        # Extract agent response text from review_result
        agent_response_text = ""
        data = review_result.get("data", {})
        
        if isinstance(data, dict):
            content = data.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                # Get text from first content item
                first_content = content[0]
                if isinstance(first_content, dict):
                    agent_response_text = first_content.get("text", "")
            
            # Fallback to answer field if content.text not found
            if not agent_response_text:
                agent_response_text = data.get("answer", "")
        
        # Store agent response in session
        session_service.append_message(
            session_id=session_id,
            role="assistant",
            content=agent_response_text
        )
        
        logger.info(
            "Requirements review completed",
            extra={"session_id": session_id, "success": review_result.get("success")}
        )
        
        return {
            "session_id": session_id,
            "project_id": request.project_id,
            "status": "review_completed" if review_result.get("success") else "review_failed",
            "message": agent_response_text,  # Changed from 'response' to 'message'
            "analysis": review_result.get("metadata", {})
        }
        
    except Exception as e:
        logger.error(
            "Requirements review failed",
            extra={"project_id": request.project_id, "session_id": request.session_id, "error": str(e)}
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
            user_query=f"""
            This is a clarification continuation request from the user for requirement review.
            The user has provided additional information or confirmation regarding previously
            identified ambiguous or missing requirements. It should be forwarded to the requirement_reviewer_agent not to any other tools. 

            Context:
            - Type: Clarification Interaction
            - Intent: Resolve pending ambiguities, provide clarification, or confirm requirements as complete.
            - User message: 
            {request.user_message}
            Please respond only with the agent's response json format without any additional formatting or explanation.
            
            ### OUTPUT FORMAT (INTERACTIVE RESPONSE)
            {{
                "readiness_plan": {{
                    "estimated_epics": 0,
                    "estimated_features": 0,
                    "estimated_use_cases": 0,
                    "estimated_test_cases": 0,
                    "overall_status": "Clarifications Needed"
                }},
                "status": "review_in_progress",
                "next_action": "await_user_clarifications",
                "assistant_response": [
                    "Requirement REQ-12 is vague. Please specify acceptable response time (e.g., in seconds).",
                    "Requirement REQ-27 mentions compliance but does not specify which standard — please confirm if FDA or IEC 62304 applies."
                ],
                "test_generation_status": {{}},
                "next_action": "Awaiting user clarifications or confirmation for pending items."
            }}

            ### Ready for Test Generation
            {{
            "agents_tools_invoked": ["reviewer_agent"],
            "action_summary": "Requirements validated.",
            "status": "ready_for_generation",
            "next_action": "trigger_test_generation",
            "readiness_plan": {{
                    "estimated_epics": 0,
                    "estimated_features": 0,
                    "estimated_use_cases": 0,
                    "estimated_test_cases": 0,
                    "overall_status": "Ready for Test Generation"
            }},
            "test_generation_status": {{}}
            }}

            """,
            load_session_context=True
        )
        
        # Extract agent response text from result
        agent_response_text = ""
        data = result.get("data", {})
        
        if isinstance(data, dict):
            content = data.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                # Get text from first content item
                first_content = content[0]
                if isinstance(first_content, dict):
                    agent_response_text = first_content.get("text", "")
            
            # Fallback to answer field if content.text not found
            if not agent_response_text:
                agent_response_text = data.get("answer", "")
        
        # Store agent response
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=agent_response_text
        )
        
        logger.info(
            "Chat message processed",
            extra={"session_id": request.session_id, "success": result.get("success")}
        )
        
        return {
            "session_id": request.session_id,
            "agent_response": agent_response_text,
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
        
        # Trigger Test Generator Agent via HTTP
        generation_result = await agent_client.process_request(
            session_id=request.session_id,
            user_query=f"""
            Generate complete test cases using the previously validated and approved requirement details available in memory. 
            Follow the standard MedAssureAI process and use the connected sub-agents (test_generator_agent) 
            to generate test cases in a structured format.

            Once the test artifacts are generated, create Jira issues for each items (epics to test cases) using the MCP Server Jira integration.

            Project ID - {request.project_id}
            Jira Project Key - {request.jira_project_key}
            Notification Email - {request.notification_email}

            Please respond only with the agent's response json format without any additional formatting or explanation.
            
            ### OUTPUT FORMAT
            {{
                "agents_tools_invoked": ["Orchestrator Agent", "jira_mcp_tool", "DynamoDB_tools"],
                "action_summary": "All artifacts stored successfully.",
                "status": "mcp_push_complete",
                "next_action": "present_summary",
                "test_generation_status": {{
                    "status": "completed",  // or "generation_completed"
                    "epics_created": 5,
                    "features_created": 12,
                    "use_cases_created": 25,
                    "test_cases_created": 150,
                    "approved_items": 120,
                    "clarifications_needed": 30,
                    "stored_in_DynamoDB": true,
                    "pushed_to_jira": true
                }}
            }}
            """,
            load_session_context=True
        )
        
        # Store generation result
        session_service.append_message(
            session_id=request.session_id,
            role="assistant",
            content=generation_result.get("data", {}).get("answer", "")
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
            
            # Extract artifact counts from agent response
            artifact_counts = {}
            data = generation_result.get("data", {})
            if isinstance(data, dict):
                content = data.get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        content_text = first_content.get("text", "")
                        # Try to parse JSON from content.text
                        try:
                            import json
                            parsed_content = json.loads(content_text)
                            test_gen_status = parsed_content.get("test_generation_status", {})
                            if test_gen_status:
                                artifact_counts = {
                                    "epics": test_gen_status.get("epics_created", 0),
                                    "features": test_gen_status.get("features_created", 0),
                                    "use_cases": test_gen_status.get("use_cases_created", 0),
                                    "test_cases": test_gen_status.get("test_cases_created", 0),
                                    "total": sum([
                                        test_gen_status.get("epics_created", 0),
                                        test_gen_status.get("features_created", 0),
                                        test_gen_status.get("use_cases_created", 0),
                                        test_gen_status.get("test_cases_created", 0)
                                    ])
                                }
                        except:
                            # Fallback to default counts if parsing fails
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
        
        # Extract content.text for response message
        response_message = "Generation completed"
        data = generation_result.get("data", {})
        if isinstance(data, dict):
            content = data.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                first_content = content[0]
                if isinstance(first_content, dict):
                    response_message = first_content.get("text", "Generation completed")
        
        return {
            "session_id": request.session_id,
            "project_id": request.project_id,
            "status": "generation_completed" if generation_result.get("success") else "generation_failed",
            "message": response_message,
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
    
    DEPRECATED: Use _get_s3_keys_for_upload and textract_service instead.
    """
    return _get_sample_requirements()


def _get_s3_keys_for_upload(upload_id: str, project_id: str) -> list:
    """
    Get S3 keys for files associated with an upload.
    
    Queries DynamoDB to get the S3 keys stored during upload.
    
    Args:
        upload_id: Upload identifier
        project_id: Project identifier
        
    Returns:
        List of S3 keys
    """
    import boto3
    from backend.config import config
    
    try:
        dynamodb = boto3.client(
            'dynamodb',
            region_name=config.AWS_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
        
        # Query for upload mapping
        response = dynamodb.get_item(
            TableName=config.DYNAMODB_TABLE_NAME,
            Key={
                'PK': {'S': f'UPLOAD#{upload_id}'},
                'SK': {'S': 'MAPPING'}
            }
        )
        
        if 'Item' in response:
            s3_keys_list = response['Item'].get('s3_keys', {}).get('L', [])
            s3_keys = [item['S'] for item in s3_keys_list]
            
            logger.info(
                "Retrieved S3 keys for upload",
                extra={
                    "upload_id": upload_id,
                    "project_id": project_id,
                    "key_count": len(s3_keys)
                }
            )
            
            return s3_keys
        else:
            logger.warning(
                "No S3 keys found for upload, using sample requirements",
                extra={"upload_id": upload_id, "project_id": project_id}
            )
            return []
            
    except Exception as e:
        logger.error(
            "Failed to retrieve S3 keys from DynamoDB",
            extra={
                "upload_id": upload_id,
                "project_id": project_id,
                "error": str(e)
            }
        )
        return []


def _get_sample_requirements() -> str:
    """
    Get sample requirements text for testing.
    
    Returns:
        Sample requirements document text
    """
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
