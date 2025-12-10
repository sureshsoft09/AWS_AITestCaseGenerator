"""
AWS Lambda function to trigger Textract document text detection.
Triggered by S3 object creation events in the ingest bucket.
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
textract = boto3.client('textract')
sns = boto3.client('sns')
dynamodb = boto3.client('dynamodb')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'MedAssureAI_Artifacts')
SNS_ROLE_ARN = os.environ.get('SNS_ROLE_ARN')


def lambda_handler(event, context):
    """
    Lambda handler for S3 object creation events.
    Triggers Textract document text detection for uploaded files.
    
    Args:
        event: S3 event notification
        context: Lambda context
        
    Returns:
        Response with processing status
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Process each S3 record
        for record in event['Records']:
            # Extract S3 information
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing file: s3://{bucket}/{key}")
            
            # Extract project_id and file_id from S3 key
            # Expected format: projects/{project_id}/documents/{file_id}/{filename}
            key_parts = key.split('/')
            if len(key_parts) < 4 or key_parts[0] != 'projects':
                print(f"Invalid S3 key format: {key}")
                continue
            
            project_id = key_parts[1]
            file_id = key_parts[3]
            
            # Check if file is a supported document type
            if not is_supported_document(key):
                print(f"Unsupported document type: {key}")
                update_file_status(project_id, file_id, 'unsupported_format')
                continue
            
            # Start Textract document text detection
            try:
                response = start_textract_detection(bucket, key, file_id)
                job_id = response['JobId']
                
                print(f"Textract job started: {job_id} for file: {key}")
                
                # Update file status in DynamoDB
                update_file_status(
                    project_id=project_id,
                    file_id=file_id,
                    status='textract_processing',
                    textract_job_id=job_id
                )
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                print(f"Textract error: {error_code} - {error_message}")
                
                update_file_status(
                    project_id=project_id,
                    file_id=file_id,
                    status='textract_failed',
                    error_message=error_message
                )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Textract processing initiated',
                'records_processed': len(event['Records'])
            })
        }
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing event',
                'error': str(e)
            })
        }


def is_supported_document(key: str) -> bool:
    """
    Check if the document type is supported by Textract.
    
    Args:
        key: S3 object key
        
    Returns:
        True if supported, False otherwise
    """
    supported_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
    return any(key.lower().endswith(ext) for ext in supported_extensions)


def start_textract_detection(bucket: str, key: str, file_id: str) -> dict:
    """
    Start Textract document text detection job.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        file_id: Unique file identifier
        
    Returns:
        Textract response with JobId
    """
    params = {
        'DocumentLocation': {
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        'JobTag': file_id,
        'ClientRequestToken': file_id  # Idempotency token
    }
    
    # Add SNS notification if configured
    if SNS_TOPIC_ARN and SNS_ROLE_ARN:
        params['NotificationChannel'] = {
            'SNSTopicArn': SNS_TOPIC_ARN,
            'RoleArn': SNS_ROLE_ARN
        }
    
    response = textract.start_document_text_detection(**params)
    return response


def update_file_status(
    project_id: str,
    file_id: str,
    status: str,
    textract_job_id: str = None,
    error_message: str = None
):
    """
    Update file processing status in DynamoDB.
    
    Args:
        project_id: Project identifier
        file_id: File identifier
        status: Processing status
        textract_job_id: Textract job ID (optional)
        error_message: Error message (optional)
    """
    try:
        update_expression = "SET processing_status = :status, updated_at = :updated_at"
        expression_values = {
            ':status': {'S': status},
            ':updated_at': {'S': get_timestamp()}
        }
        
        if textract_job_id:
            update_expression += ", textract_job_id = :job_id"
            expression_values[':job_id'] = {'S': textract_job_id}
        
        if error_message:
            update_expression += ", error_message = :error"
            expression_values[':error'] = {'S': error_message}
        
        dynamodb.update_item(
            TableName=DYNAMODB_TABLE_NAME,
            Key={
                'PK': {'S': f'PROJECT#{project_id}'},
                'SK': {'S': f'FILE#{file_id}'}
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        print(f"Updated file status: {file_id} -> {status}")
        
    except ClientError as e:
        print(f"Failed to update file status: {str(e)}")


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat()
