"""
Migration API endpoints for MedAssureAI.
Handles Excel test case migration.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from backend.logger import logger

# Import agents
import sys
sys.path.insert(0, '.')
from agents import MigrationAgent


router = APIRouter(prefix="/api/migrate", tags=["migrate"])

# Initialize Migration Agent
migration_agent = MigrationAgent()


class MigrateUploadResponse(BaseModel):
    """Response model for migration upload."""
    migration_id: str
    filename: str
    file_size: int
    status: str
    message: str


class MigrateProcessRequest(BaseModel):
    """Request model for migration processing."""
    migration_id: str
    project_id: str
    project_name: str
    jira_project_key: str


class MigrateProcessResponse(BaseModel):
    """Response model for migration processing."""
    migration_id: str
    project_id: str
    status: str
    message: str
    processing_started: bool


class MigrateStatusResponse(BaseModel):
    """Response model for migration status."""
    migration_id: str
    project_id: str
    status: str
    progress: dict
    report: Optional[dict] = None


@router.post("/upload", response_model=MigrateUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_migration_file(
    file: UploadFile = File(...),
):
    """
    Upload Excel file for migration.
    
    This endpoint:
    1. Validates file type (Excel: .xlsx, .xls)
    2. Validates file size (max 50MB)
    3. Saves file to temporary storage
    4. Returns migration_id for tracking
    
    Args:
        file: Excel file upload
        
    Returns:
        Upload response with migration_id
    """
    import uuid
    import os
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.xlsx', '.xls']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Expected .xlsx or .xls, got {file_ext}"
            )
        
        # Generate migration ID
        migration_id = str(uuid.uuid4())
        
        logger.info(
            "Uploading migration file",
            extra={
                "migration_id": migration_id,
                "filename": file.filename,
                "content_type": file.content_type
            }
        )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: 50MB, got: {file_size / 1024 / 1024:.2f}MB"
            )
        
        # Save file to temporary storage
        # In production, this would save to S3
        temp_file_path = f"/tmp/migration_{migration_id}{file_ext}"
        
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(
            "Migration file uploaded",
            extra={
                "migration_id": migration_id,
                "file_size": file_size,
                "temp_path": temp_file_path
            }
        )
        
        return {
            "migration_id": migration_id,
            "filename": file.filename,
            "file_size": file_size,
            "status": "uploaded",
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Migration file upload failed",
            extra={"filename": file.filename if file else "unknown", "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/process", response_model=MigrateProcessResponse)
async def process_migration(request: MigrateProcessRequest):
    """
    Process migration with Migration Agent.
    
    This endpoint:
    1. Retrieves uploaded Excel file
    2. Triggers Migration Agent to parse and process
    3. Converts Excel data to JSON format
    4. Normalizes test case fields
    5. Applies compliance mapping
    6. Detects duplicates
    7. Creates Jira issues via MCP Server
    8. Stores test cases in DynamoDB via MCP Server
    9. Generates migration report
    
    Args:
        request: Migration process request with project details
        
    Returns:
        Process response with migration status
    """
    from backend.services.session_service import session_service
    import os
    
    try:
        logger.info(
            "Starting migration processing",
            extra={
                "migration_id": request.migration_id,
                "project_id": request.project_id
            }
        )
        
        # Get file path
        # Check both .xlsx and .xls extensions
        temp_file_path = None
        for ext in ['.xlsx', '.xls']:
            path = f"/tmp/migration_{request.migration_id}{ext}"
            if os.path.exists(path):
                temp_file_path = path
                break
        
        if not temp_file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration file not found for ID: {request.migration_id}"
            )
        
        # Create session for tracking
        session_id = request.migration_id
        session_service.create_session(
            session_id=session_id,
            session_type="migration",
            project_id=request.project_id,
            context={
                "migration_id": request.migration_id,
                "project_id": request.project_id,
                "project_name": request.project_name,
                "jira_project_key": request.jira_project_key,
                "file_path": temp_file_path,
                "phase": "processing",
                "status": "processing"
            }
        )
        
        # Trigger Migration Agent
        migration_input = f"""
        Migrate test cases from Excel file to the system.
        
        File path: {temp_file_path}
        Project ID: {request.project_id}
        Project Name: {request.project_name}
        Jira Project Key: {request.jira_project_key}
        
        Please:
        1. Parse the Excel file
        2. Convert to JSON format
        3. Normalize fields
        4. Apply compliance mapping
        5. Detect duplicates
        6. Create Jira issues
        7. Store in DynamoDB
        8. Generate migration report
        """
        
        migration_result = migration_agent.run(
            user_input=migration_input,
            context={
                "migration_id": request.migration_id,
                "project_id": request.project_id,
                "project_name": request.project_name,
                "jira_project_key": request.jira_project_key,
                "file_path": temp_file_path
            }
        )
        
        # Store migration result in session
        session_service.append_message(
            session_id=session_id,
            role="assistant",
            content=migration_result.get("answer", "")
        )
        
        # Update session status
        session_service.update_context(
            session_id=session_id,
            context_updates={
                "status": "completed" if migration_result.get("success") else "failed",
                "migration_completed": migration_result.get("success", False)
            }
        )
        
        logger.info(
            "Migration processing completed",
            extra={
                "migration_id": request.migration_id,
                "success": migration_result.get("success")
            }
        )
        
        return {
            "migration_id": request.migration_id,
            "project_id": request.project_id,
            "status": "completed" if migration_result.get("success") else "failed",
            "message": migration_result.get("answer", "Migration processing completed"),
            "processing_started": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Migration processing failed",
            extra={"migration_id": request.migration_id, "error": str(e)}
        )
        
        # Update session status to failed
        try:
            session_service.update_context(
                session_id=request.migration_id,
                context_updates={"status": "failed", "error": str(e)}
            )
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration processing failed: {str(e)}"
        )


@router.get("/status/{migration_id}", response_model=MigrateStatusResponse)
async def get_migration_status(migration_id: str):
    """
    Get migration progress and results.
    
    Args:
        migration_id: Migration identifier
        
    Returns:
        Status response with progress and report
    """
    from backend.services.session_service import session_service
    
    try:
        # Get session
        session = session_service.get_session(migration_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Migration {migration_id} not found"
            )
        
        context = session.get("context", {})
        project_id = context.get("project_id", "unknown")
        status_value = context.get("status", "unknown")
        phase = context.get("phase", "processing")
        
        # Build progress information
        progress = {
            "phase": phase,
            "status": status_value,
            "migration_completed": context.get("migration_completed", False),
            "error": context.get("error")
        }
        
        # Get migration report if completed
        report = None
        if context.get("migration_completed"):
            report = _generate_migration_report(migration_id, project_id)
        
        return {
            "migration_id": migration_id,
            "project_id": project_id,
            "status": status_value,
            "progress": progress,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get migration status",
            extra={"migration_id": migration_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration status: {str(e)}"
        )


def _generate_migration_report(migration_id: str, project_id: str) -> dict:
    """
    Generate migration report with success/failure counts.
    
    In production, this would query DynamoDB for actual counts.
    """
    # Simulate migration report
    return {
        "migration_id": migration_id,
        "project_id": project_id,
        "total_extracted": 25,
        "total_converted": 25,
        "total_normalized": 25,
        "duplicates_found": 2,
        "jira_issues_created": 23,
        "dynamodb_records_stored": 23,
        "success_count": 23,
        "failure_count": 2,
        "status": "completed",
        "summary": "Successfully migrated 23 test cases, 2 duplicates skipped"
    }
