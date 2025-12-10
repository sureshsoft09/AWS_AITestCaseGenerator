"""
Unit tests for File Upload Service.
Tests file validation, S3 upload, and metadata storage.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.services.file_upload_service import FileUploadService


class TestFileUploadService:
    """Test suite for FileUploadService."""
    
    @pytest.fixture
    def service(self):
        """Create FileUploadService instance with mocked AWS clients."""
        with patch('backend.services.file_upload_service.boto3'):
            service = FileUploadService()
            service.s3_client = Mock()
            service.dynamodb_client = Mock()
            return service
    
    def test_validate_file_success_pdf(self, service):
        """Test successful validation of PDF file."""
        result = service.validate_file(
            filename="test.pdf",
            file_size=1024,
            content_type="application/pdf"
        )
        
        assert result["valid"] is True
        assert result["filename"] == "test.pdf"
        assert result["file_size"] == 1024
        assert result["content_type"] == "application/pdf"
    
    def test_validate_file_success_docx(self, service):
        """Test successful validation of Word document."""
        result = service.validate_file(
            filename="test.docx",
            file_size=2048,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        assert result["valid"] is True
        assert result["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_validate_file_exceeds_size_limit(self, service):
        """Test validation fails when file exceeds size limit."""
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            service.validate_file(
                filename="large.pdf",
                file_size=51 * 1024 * 1024,  # 51MB
                content_type="application/pdf"
            )
    
    def test_validate_file_empty(self, service):
        """Test validation fails for empty file."""
        with pytest.raises(ValueError, match="File is empty"):
            service.validate_file(
                filename="empty.pdf",
                file_size=0,
                content_type="application/pdf"
            )
    
    def test_validate_file_invalid_type(self, service):
        """Test validation fails for invalid file type."""
        with pytest.raises(ValueError, match="not allowed"):
            service.validate_file(
                filename="test.txt",
                file_size=1024,
                content_type="text/plain"
            )
    
    def test_upload_file_small_success(self, service):
        """Test successful upload of small file (< 5MB)."""
        file_content = b"test content"
        filename = "test.pdf"
        project_id = "test_project"
        
        # Mock S3 put_object
        service.s3_client.put_object.return_value = {}
        
        # Mock DynamoDB put_item
        service.dynamodb_client.put_item.return_value = {}
        
        result = service.upload_file(
            file_content=file_content,
            filename=filename,
            project_id=project_id,
            content_type="application/pdf"
        )
        
        # Verify result
        assert result["filename"] == filename
        assert result["file_size"] == len(file_content)
        assert result["status"] == "uploaded"
        assert "file_id" in result
        assert "s3_key" in result
        
        # Verify S3 put_object was called
        service.s3_client.put_object.assert_called_once()
        call_args = service.s3_client.put_object.call_args
        assert call_args[1]["Body"] == file_content
        assert call_args[1]["ContentType"] == "application/pdf"
        
        # Verify DynamoDB put_item was called
        service.dynamodb_client.put_item.assert_called_once()
    
    def test_upload_file_large_multipart(self, service):
        """Test multipart upload for large file (> 5MB)."""
        # Create 6MB file
        file_content = b"x" * (6 * 1024 * 1024)
        filename = "large.pdf"
        project_id = "test_project"
        
        # Mock multipart upload
        service.s3_client.create_multipart_upload.return_value = {
            'UploadId': 'test-upload-id'
        }
        service.s3_client.upload_part.return_value = {
            'ETag': 'test-etag'
        }
        service.s3_client.complete_multipart_upload.return_value = {}
        service.dynamodb_client.put_item.return_value = {}
        
        result = service.upload_file(
            file_content=file_content,
            filename=filename,
            project_id=project_id,
            content_type="application/pdf"
        )
        
        # Verify multipart upload was used
        service.s3_client.create_multipart_upload.assert_called_once()
        assert service.s3_client.upload_part.call_count >= 1
        service.s3_client.complete_multipart_upload.assert_called_once()
        
        # Verify result
        assert result["filename"] == filename
        assert result["status"] == "uploaded"
    
    def test_upload_file_validation_failure(self, service):
        """Test upload fails with invalid file."""
        with pytest.raises(ValueError):
            service.upload_file(
                file_content=b"test",
                filename="test.txt",
                project_id="test_project",
                content_type="text/plain"
            )
    
    def test_generate_presigned_url(self, service):
        """Test presigned URL generation."""
        filename = "test.pdf"
        project_id = "test_project"
        content_type = "application/pdf"
        
        service.s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"
        
        result = service.generate_presigned_upload_url(
            filename=filename,
            project_id=project_id,
            content_type=content_type
        )
        
        assert "file_id" in result
        assert result["presigned_url"] == "https://s3.amazonaws.com/presigned-url"
        assert result["method"] == "PUT"
        assert result["headers"]["Content-Type"] == content_type
        
        service.s3_client.generate_presigned_url.assert_called_once()
    
    def test_get_file_metadata_success(self, service):
        """Test retrieving file metadata from DynamoDB."""
        file_id = "test-file-id"
        project_id = "test_project"
        
        service.dynamodb_client.get_item.return_value = {
            'Item': {
                'file_id': {'S': file_id},
                'filename': {'S': 'test.pdf'},
                'file_size': {'N': '1024'},
                'content_type': {'S': 'application/pdf'},
                's3_key': {'S': 'projects/test_project/documents/test-file-id/test.pdf'},
                's3_bucket': {'S': 'test-bucket'},
                'project_id': {'S': project_id},
                'upload_time': {'S': '2024-01-01T00:00:00Z'},
                'processing_status': {'S': 'uploaded'},
                'created_at': {'S': '2024-01-01T00:00:00Z'},
                'updated_at': {'S': '2024-01-01T00:00:00Z'}
            }
        }
        
        result = service.get_file_metadata(file_id, project_id)
        
        assert result is not None
        assert result['file_id'] == file_id
        assert result['filename'] == 'test.pdf'
        assert result['file_size'] == 1024
        assert result['processing_status'] == 'uploaded'
    
    def test_get_file_metadata_not_found(self, service):
        """Test retrieving non-existent file metadata."""
        service.dynamodb_client.get_item.return_value = {}
        
        result = service.get_file_metadata("nonexistent", "test_project")
        
        assert result is None
    
    def test_multipart_upload_abort_on_failure(self, service):
        """Test multipart upload is aborted on failure."""
        file_content = b"x" * (6 * 1024 * 1024)
        s3_key = "test-key"
        content_type = "application/pdf"
        
        service.s3_client.create_multipart_upload.return_value = {
            'UploadId': 'test-upload-id'
        }
        service.s3_client.upload_part.side_effect = Exception("Upload failed")
        
        with pytest.raises(Exception, match="Upload failed"):
            service._multipart_upload(s3_key, file_content, content_type)
        
        # Verify abort was called
        service.s3_client.abort_multipart_upload.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
