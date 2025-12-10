"""
Unit tests for Textract Trigger Lambda function.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Set environment variables before importing lambda_function
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
os.environ['SNS_ROLE_ARN'] = 'arn:aws:iam::123456789012:role/test-role'
os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'

# Mock boto3 clients before importing lambda_function
with patch('boto3.client'):
    import lambda_function


class TestTextractTriggerLambda:
    """Test suite for Textract Trigger Lambda."""
    
    @pytest.fixture
    def s3_event(self):
        """Create sample S3 event."""
        return {
            'Records': [
                {
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': 'projects/test_project/documents/file-123/test.pdf'}
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_clients(self):
        """Mock AWS clients."""
        with patch('lambda_function.textract') as mock_textract, \
             patch('lambda_function.dynamodb') as mock_dynamodb:
            yield {
                'textract': mock_textract,
                'dynamodb': mock_dynamodb
            }
    
    def test_is_supported_document_pdf(self):
        """Test PDF is recognized as supported."""
        assert lambda_function.is_supported_document('test.pdf') is True
        assert lambda_function.is_supported_document('test.PDF') is True
    
    def test_is_supported_document_images(self):
        """Test images are recognized as supported."""
        assert lambda_function.is_supported_document('test.png') is True
        assert lambda_function.is_supported_document('test.jpg') is True
        assert lambda_function.is_supported_document('test.jpeg') is True
        assert lambda_function.is_supported_document('test.tiff') is True
    
    def test_is_supported_document_unsupported(self):
        """Test unsupported formats are rejected."""
        assert lambda_function.is_supported_document('test.txt') is False
        assert lambda_function.is_supported_document('test.docx') is False
        assert lambda_function.is_supported_document('test.xlsx') is False
    
    def test_start_textract_detection(self, mock_clients):
        """Test starting Textract detection."""
        mock_clients['textract'].start_document_text_detection.return_value = {
            'JobId': 'test-job-123'
        }
        
        result = lambda_function.start_textract_detection(
            bucket='test-bucket',
            key='test.pdf',
            file_id='file-123'
        )
        
        assert result['JobId'] == 'test-job-123'
        mock_clients['textract'].start_document_text_detection.assert_called_once()
        
        call_args = mock_clients['textract'].start_document_text_detection.call_args[1]
        assert call_args['DocumentLocation']['S3Object']['Bucket'] == 'test-bucket'
        assert call_args['DocumentLocation']['S3Object']['Name'] == 'test.pdf'
        assert call_args['JobTag'] == 'file-123'
        assert call_args['ClientRequestToken'] == 'file-123'
    
    def test_update_file_status_success(self, mock_clients):
        """Test updating file status in DynamoDB."""
        lambda_function.update_file_status(
            project_id='test_project',
            file_id='file-123',
            status='textract_processing',
            textract_job_id='job-456'
        )
        
        mock_clients['dynamodb'].update_item.assert_called_once()
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        
        assert call_args['Key']['PK']['S'] == 'PROJECT#test_project'
        assert call_args['Key']['SK']['S'] == 'FILE#file-123'
        assert ':status' in call_args['ExpressionAttributeValues']
        assert call_args['ExpressionAttributeValues'][':status']['S'] == 'textract_processing'
    
    def test_lambda_handler_success(self, s3_event, mock_clients):
        """Test successful Lambda execution."""
        mock_clients['textract'].start_document_text_detection.return_value = {
            'JobId': 'test-job-123'
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_function.lambda_handler(s3_event, None)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['records_processed'] == 1
        
        # Verify Textract was called
        mock_clients['textract'].start_document_text_detection.assert_called_once()
        
        # Verify DynamoDB was updated
        mock_clients['dynamodb'].update_item.assert_called_once()
    
    def test_lambda_handler_unsupported_format(self, mock_clients):
        """Test handling of unsupported file format."""
        event = {
            'Records': [
                {
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': 'projects/test_project/documents/file-123/test.txt'}
                    }
                }
            ]
        }
        
        result = lambda_function.lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        
        # Textract should not be called for unsupported format
        mock_clients['textract'].start_document_text_detection.assert_not_called()
        
        # DynamoDB should be updated with unsupported status
        mock_clients['dynamodb'].update_item.assert_called_once()
    
    def test_lambda_handler_invalid_key_format(self, mock_clients):
        """Test handling of invalid S3 key format."""
        event = {
            'Records': [
                {
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': 'invalid/key/format.pdf'}
                    }
                }
            ]
        }
        
        result = lambda_function.lambda_handler(event, None)
        
        assert result['statusCode'] == 200
        
        # Should not process invalid key format
        mock_clients['textract'].start_document_text_detection.assert_not_called()
    
    def test_lambda_handler_textract_error(self, s3_event, mock_clients):
        """Test handling of Textract API error."""
        from botocore.exceptions import ClientError
        
        mock_clients['textract'].start_document_text_detection.side_effect = ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
            'StartDocumentTextDetection'
        )
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_function.lambda_handler(s3_event, None)
        
        assert result['statusCode'] == 200
        
        # DynamoDB should be updated with failed status
        mock_clients['dynamodb'].update_item.assert_called()
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert ':status' in call_args['ExpressionAttributeValues']
        assert call_args['ExpressionAttributeValues'][':status']['S'] == 'textract_failed'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
