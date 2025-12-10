"""
File Upload API endpoints for MedAssureAI.
Handles document upload requests from frontend.
"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.services.file_upload_service import file_upload_service
from backend.logger import logger


router = APIRouter(prefix="/api/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Response model for file upload."""
    upload_id: str
    project_id: str
    project_name: str
    jira_project_key: Optional[str]
    notification_email: Optional[str]
    files: List[dict]


class PresignedUrlRequest(BaseModel):
    """Request model for presigned URL generation."""
    filename: str
    project_id: str
    content_type: str


class PresignedUrlResponse(BaseModel):
    """Response model for presigned URL."""
    file_id: str
    presigned_url: str
    s3_key: str
    expiration: int
    method: str
    headers: dict


@router.post("/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = File(...),
    project_name: str = Form(...),
    jira_project_key: Optional[str] = Form(None),
    notification_email: Optional[EmailStr] = Form(None)
):
    """
    Upload requirement documents for processing.
    
    Args:
        files: List of uploaded files (PDF or Word documents)
        project_name: Name of the project
        jira_project_key: Jira project key for issue creation
        notification_email: Email for completion notifications
        
    Returns:
        Upload response with file details
        
    Raises:
        HTTPException: If validation or upload fails
    """
    import uuid
    
    # Generate unique project ID
    project_id = f"{project_name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
    upload_id = str(uuid.uuid4())
    
    logger.info(
        "Processing file upload request",
        extra={
            "upload_id": upload_id,
            "project_id": project_id,
            "project_name": project_name,
            "file_count": len(files)
        }
    )
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            
            # Upload file
            result = file_upload_service.upload_file(
                file_content=content,
                filename=file.filename,
                project_id=project_id,
                content_type=file.content_type
            )
            
            uploaded_files.append(result)
            
        except ValueError as e:
            # Validation error
            logger.warning(
                "File validation failed",
                extra={
                    "file_name": file.filename,
                    "error": str(e)
                }
            )
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "status": "validation_failed"
            })
            
        except Exception as e:
            # Upload error
            logger.error(
                "File upload failed",
                extra={
                    "file_name": file.filename,
                    "error": str(e)
                }
            )
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "status": "upload_failed"
            })
    
    # If all files failed, return error
    if not uploaded_files and errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "All file uploads failed",
                "errors": errors
            }
        )
    
    # Store project metadata in DynamoDB
    try:
        _store_project_metadata(
            project_id=project_id,
            project_name=project_name,
            jira_project_key=jira_project_key,
            notification_email=notification_email,
            upload_id=upload_id,
            file_count=len(uploaded_files)
        )
    except Exception as e:
        logger.error(
            "Failed to store project metadata",
            extra={"project_id": project_id, "error": str(e)}
        )
        # Don't fail the request - files are already uploaded
    
    logger.info(
        "File upload completed",
        extra={
            "upload_id": upload_id,
            "project_id": project_id,
            "successful_uploads": len(uploaded_files),
            "failed_uploads": len(errors)
        }
    )
    
    response = {
        "upload_id": upload_id,
        "project_id": project_id,
        "project_name": project_name,
        "jira_project_key": jira_project_key,
        "notification_email": notification_email,
        "files": uploaded_files
    }
    
    # Include errors if any
    if errors:
        response["errors"] = errors
    
    return response


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(request: PresignedUrlRequest):
    """
    Generate presigned URL for direct client-side upload to S3.
    
    This endpoint allows the frontend to upload large files directly to S3
    without going through the backend, improving upload performance.
    
    Args:
        request: Presigned URL request with file details
        
    Returns:
        Presigned URL and upload instructions
        
    Raises:
        HTTPException: If URL generation fails
    """
    try:
        # Validate file type
        file_upload_service.validate_file(
            filename=request.filename,
            file_size=1,  # Size will be validated on actual upload
            content_type=request.content_type
        )
        
        result = file_upload_service.generate_presigned_upload_url(
            filename=request.filename,
            project_id=request.project_id,
            content_type=request.content_type
        )
        
        logger.info(
            "Generated presigned URL",
            extra={
                "file_id": result["file_id"],
                "file_name": request.filename,
                "project_id": request.project_id
            }
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to generate presigned URL",
            extra={"file_name": request.filename, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


@router.get("/{project_id}/files")
async def get_project_files(project_id: str):
    """
    Get all files associated with a project.
    
    Args:
        project_id: Project identifier
        
    Returns:
        List of file metadata
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
        
        # Query all files for the project
        response = dynamodb.query(
            TableName=config.DYNAMODB_TABLE_NAME,
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': {'S': f'PROJECT#{project_id}'},
                ':sk': {'S': 'FILE#'}
            }
        )
        
        files = []
        for item in response.get('Items', []):
            files.append({
                'file_id': item['file_id']['S'],
                'filename': item['filename']['S'],
                'file_size': int(item['file_size']['N']),
                'content_type': item['content_type']['S'],
                'upload_time': item['upload_time']['S'],
                'processing_status': item.get('processing_status', {}).get('S', 'unknown')
            })
        
        return {"project_id": project_id, "files": files}
        
    except Exception as e:
        logger.error(
            "Failed to retrieve project files",
            extra={"project_id": project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project files: {str(e)}"
        )


def _store_project_metadata(
    project_id: str,
    project_name: str,
    jira_project_key: Optional[str],
    notification_email: Optional[str],
    upload_id: str,
    file_count: int
):
    """
    Store project metadata in DynamoDB.
    
    Args:
        project_id: Unique project identifier
        project_name: Project name
        jira_project_key: Jira project key
        notification_email: Email for notifications
        upload_id: Upload session ID
        file_count: Number of uploaded files
    """
    import boto3
    from datetime import datetime
    from backend.config import config
    
    dynamodb = boto3.client(
        'dynamodb',
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
    )
    
    timestamp = datetime.utcnow().isoformat()
    
    item = {
        'PK': {'S': f'PROJECT#{project_id}'},
        'SK': {'S': 'METADATA'},
        'entity_type': {'S': 'project'},
        'project_id': {'S': project_id},
        'project_name': {'S': project_name},
        'upload_id': {'S': upload_id},
        'file_count': {'N': str(file_count)},
        'status': {'S': 'documents_uploaded'},
        'created_at': {'S': timestamp},
        'updated_at': {'S': timestamp}
    }
    
    if jira_project_key:
        item['jira_project_key'] = {'S': jira_project_key}
    
    if notification_email:
        item['notification_email'] = {'S': notification_email}
    
    dynamodb.put_item(
        TableName=config.DYNAMODB_TABLE_NAME,
        Item=item
    )
    
    logger.info(
        "Project metadata stored",
        extra={"project_id": project_id, "project_name": project_name}
    )
