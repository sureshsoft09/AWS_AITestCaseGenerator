"""
File Upload Service for MedAssureAI.
Handles document upload, validation, and storage in S3.
"""
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError
from backend.config import config
from backend.logger import logger


class FileUploadService:
    """Service for handling file uploads to S3."""
    
    # Allowed MIME types for documents
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
    }
    
    # Maximum file size: 50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    # Multipart upload threshold: 5MB
    MULTIPART_THRESHOLD = 5 * 1024 * 1024  # 5MB in bytes
    
    def __init__(self):
        """Initialize the file upload service."""
        # Use AWS profile if credentials are not explicitly provided
        # This allows boto3 to use default credential chain (env vars, profile, IAM role, etc.)
        if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
            # Build client kwargs
            client_kwargs = {
                'region_name': config.AWS_REGION,
                'aws_access_key_id': config.AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': config.AWS_SECRET_ACCESS_KEY
            }
            
            # Add session token if present (for temporary credentials)
            if config.AWS_SESSION_TOKEN:
                client_kwargs['aws_session_token'] = config.AWS_SESSION_TOKEN
            
            self.s3_client = boto3.client('s3', **client_kwargs)
            self.dynamodb_client = boto3.client('dynamodb', **client_kwargs)
        else:
            # Use default credential chain (profile, IAM role, etc.)
            self.s3_client = boto3.client('s3', region_name=config.AWS_REGION)
            self.dynamodb_client = boto3.client('dynamodb', region_name=config.AWS_REGION)
        
        self.ingest_bucket = config.S3_INGEST_BUCKET
        self.table_name = config.DYNAMODB_TABLE_NAME
    
    def validate_file(self, filename: str, file_size: int, content_type: Optional[str] = None) -> Dict[str, any]:
        """
        Validate uploaded file against requirements.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            content_type: MIME type of the file
            
        Returns:
            Dict with validation result
            
        Raises:
            ValueError: If validation fails
        """
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_size} bytes exceeds maximum allowed size of {self.MAX_FILE_SIZE} bytes (50MB)"
            )
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Determine MIME type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
        
        # Check MIME type
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"File type '{content_type}' is not allowed. "
                f"Allowed types: PDF, Word (.doc, .docx)"
            )
        
        logger.info(
            "File validation successful",
            extra={
                "file_name": filename,
                "file_size": file_size,
                "content_type": content_type
            }
        )
        
        return {
            "valid": True,
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type
        }
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        project_id: str,
        content_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Upload file to S3 ingest bucket.
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            project_id: Project ID to associate with the file
            content_type: MIME type of the file
            
        Returns:
            Dict with upload details including file_id
            
        Raises:
            ValueError: If validation fails
            Exception: If upload fails
        """
        # Validate file
        file_size = len(file_content)
        self.validate_file(filename, file_size, content_type)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Determine content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
        
        # Construct S3 key with project organization
        s3_key = f"projects/{project_id}/documents/{file_id}/{filename}"
        
        try:
            # Check if multipart upload is needed
            if file_size > self.MULTIPART_THRESHOLD:
                logger.info(
                    "Using multipart upload for large file",
                    extra={"file_id": file_id, "file_size": file_size}
                )
                self._multipart_upload(s3_key, file_content, content_type)
            else:
                # Standard upload for smaller files
                self.s3_client.put_object(
                    Bucket=self.ingest_bucket,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata={
                        'original_filename': filename,
                        'file_id': file_id,
                        'project_id': project_id,
                        'upload_time': datetime.utcnow().isoformat()
                    }
                )
            
            upload_time = datetime.utcnow().isoformat()
            
            logger.info(
                "File uploaded successfully to S3",
                extra={
                    "file_id": file_id,
                    "file_name": filename,
                    "s3_key": s3_key,
                    "bucket": self.ingest_bucket
                }
            )
            
            # Store file metadata in DynamoDB
            self._store_file_metadata(
                file_id=file_id,
                filename=filename,
                file_size=file_size,
                content_type=content_type,
                s3_key=s3_key,
                project_id=project_id,
                upload_time=upload_time
            )
            
            return {
                "file_id": file_id,
                "filename": filename,
                "file_size": file_size,
                "content_type": content_type,
                "s3_key": s3_key,
                "s3_bucket": self.ingest_bucket,
                "upload_time": upload_time,
                "status": "uploaded"
            }
            
        except ClientError as e:
            logger.error(
                "S3 upload failed",
                extra={
                    "file_id": file_id,
                    "file_name": filename,
                    "error": str(e)
                }
            )
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    def _multipart_upload(self, s3_key: str, file_content: bytes, content_type: str):
        """
        Perform multipart upload for large files.
        
        Args:
            s3_key: S3 object key
            file_content: Binary content of the file
            content_type: MIME type
        """
        # Initiate multipart upload
        multipart_upload = self.s3_client.create_multipart_upload(
            Bucket=self.ingest_bucket,
            Key=s3_key,
            ContentType=content_type
        )
        upload_id = multipart_upload['UploadId']
        
        try:
            # Upload parts (5MB chunks)
            part_size = 5 * 1024 * 1024  # 5MB
            parts = []
            part_number = 1
            
            for i in range(0, len(file_content), part_size):
                part_data = file_content[i:i + part_size]
                
                response = self.s3_client.upload_part(
                    Bucket=self.ingest_bucket,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=part_data
                )
                
                parts.append({
                    'PartNumber': part_number,
                    'ETag': response['ETag']
                })
                
                part_number += 1
            
            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=self.ingest_bucket,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            logger.info(
                "Multipart upload completed",
                extra={"s3_key": s3_key, "parts_count": len(parts)}
            )
            
        except Exception as e:
            # Abort multipart upload on failure
            self.s3_client.abort_multipart_upload(
                Bucket=self.ingest_bucket,
                Key=s3_key,
                UploadId=upload_id
            )
            logger.error(
                "Multipart upload failed and aborted",
                extra={"s3_key": s3_key, "error": str(e)}
            )
            raise
    
    def _store_file_metadata(
        self,
        file_id: str,
        filename: str,
        file_size: int,
        content_type: str,
        s3_key: str,
        project_id: str,
        upload_time: str
    ):
        """
        Store file metadata in DynamoDB.
        
        Args:
            file_id: Unique file identifier
            filename: Original filename
            file_size: Size in bytes
            content_type: MIME type
            s3_key: S3 object key
            project_id: Associated project ID
            upload_time: ISO format timestamp
        """
        try:
            self.dynamodb_client.put_item(
                TableName=self.table_name,
                Item={
                    'PK': {'S': f'PROJECT#{project_id}'},
                    'SK': {'S': f'FILE#{file_id}'},
                    'GSI1PK': {'S': f'FILE#{file_id}'},
                    'GSI1SK': {'S': f'PROJECT#{project_id}'},
                    'entity_type': {'S': 'file'},
                    'file_id': {'S': file_id},
                    'filename': {'S': filename},
                    'file_size': {'N': str(file_size)},
                    'content_type': {'S': content_type},
                    's3_key': {'S': s3_key},
                    's3_bucket': {'S': self.ingest_bucket},
                    'project_id': {'S': project_id},
                    'upload_time': {'S': upload_time},
                    'processing_status': {'S': 'uploaded'},
                    'created_at': {'S': upload_time},
                    'updated_at': {'S': upload_time}
                }
            )
            
            logger.info(
                "File metadata stored in DynamoDB",
                extra={"file_id": file_id, "project_id": project_id}
            )
            
        except ClientError as e:
            logger.error(
                "Failed to store file metadata in DynamoDB",
                extra={"file_id": file_id, "error": str(e)}
            )
            # Don't raise - file is already in S3, metadata storage is secondary
    
    def generate_presigned_upload_url(
        self,
        filename: str,
        project_id: str,
        content_type: str,
        expiration: int = 3600
    ) -> Dict[str, any]:
        """
        Generate presigned URL for direct client-side upload to S3.
        
        Args:
            filename: Original filename
            project_id: Project ID
            content_type: MIME type
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Dict with presigned URL and upload details
        """
        file_id = str(uuid.uuid4())
        s3_key = f"projects/{project_id}/documents/{file_id}/{filename}"
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.ingest_bucket,
                    'Key': s3_key,
                    'ContentType': content_type,
                    'Metadata': {
                        'original_filename': filename,
                        'file_id': file_id,
                        'project_id': project_id,
                        'upload_time': datetime.utcnow().isoformat()
                    }
                },
                ExpiresIn=expiration
            )
            
            logger.info(
                "Generated presigned upload URL",
                extra={
                    "file_id": file_id,
                    "file_name": filename,
                    "expiration": expiration
                }
            )
            
            return {
                "file_id": file_id,
                "presigned_url": presigned_url,
                "s3_key": s3_key,
                "expiration": expiration,
                "method": "PUT",
                "headers": {
                    "Content-Type": content_type
                }
            }
            
        except ClientError as e:
            logger.error(
                "Failed to generate presigned URL",
                extra={"file_name": filename, "error": str(e)}
            )
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
    
    def get_file_metadata(self, file_id: str, project_id: str) -> Optional[Dict[str, any]]:
        """
        Retrieve file metadata from DynamoDB.
        
        Args:
            file_id: File identifier
            project_id: Project identifier
            
        Returns:
            File metadata dict or None if not found
        """
        try:
            response = self.dynamodb_client.get_item(
                TableName=self.table_name,
                Key={
                    'PK': {'S': f'PROJECT#{project_id}'},
                    'SK': {'S': f'FILE#{file_id}'}
                }
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return {
                'file_id': item['file_id']['S'],
                'filename': item['filename']['S'],
                'file_size': int(item['file_size']['N']),
                'content_type': item['content_type']['S'],
                's3_key': item['s3_key']['S'],
                's3_bucket': item['s3_bucket']['S'],
                'project_id': item['project_id']['S'],
                'upload_time': item['upload_time']['S'],
                'processing_status': item.get('processing_status', {}).get('S', 'unknown'),
                'created_at': item['created_at']['S'],
                'updated_at': item['updated_at']['S']
            }
            
        except ClientError as e:
            logger.error(
                "Failed to retrieve file metadata",
                extra={"file_id": file_id, "error": str(e)}
            )
            return None


# Create singleton instance
file_upload_service = FileUploadService()
