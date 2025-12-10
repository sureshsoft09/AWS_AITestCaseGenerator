"""
AWS Lambda function to handle Textract completion notifications.
Triggered by SNS notifications when Textract jobs complete.
Retrieves extracted text and stores it for Review Agent processing.
"""
import json
import os
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
textract = boto3.client('textract')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')
dynamodb = boto3.client('dynamodb')

# Environment variables
EXTRACTED_TEXT_BUCKET = os.environ.get('EXTRACTED_TEXT_BUCKET')
REVIEW_AGENT_QUEUE_URL = os.environ.get('REVIEW_AGENT_QUEUE_URL')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'MedAssureAI_Artifacts')


def lambda_handler(event, context):
    """
    Lambda handler for SNS notifications from Textract.
    Retrieves extracted text and stores it for processing.
    
    Args:
        event: SNS event notification
        context: Lambda context
        
    Returns:
        Response with processing status
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Process each SNS record
        for record in event['Records']:
            # Parse SNS message
            message = json.loads(record['Sns']['Message'])
            
            status = message.get('Status')
            job_id = message.get('JobId')
            
            print(f"Textract job {job_id} status: {status}")
            
            if status == 'SUCCEEDED':
                # Retrieve and process extracted text
                process_textract_results(job_id)
            elif status == 'FAILED':
                # Handle failure
                handle_textract_failure(job_id, message)
            else:
                print(f"Unknown status: {status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Textract completion processed',
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


def process_textract_results(job_id: str):
    """
    Retrieve and process Textract results.
    
    Args:
        job_id: Textract job ID
    """
    try:
        # Get file information from DynamoDB using job_id
        file_info = get_file_by_job_id(job_id)
        if not file_info:
            print(f"File not found for job_id: {job_id}")
            return
        
        project_id = file_info['project_id']
        file_id = file_info['file_id']
        
        print(f"Processing results for file: {file_id}")
        
        # Retrieve Textract results
        extracted_text = retrieve_textract_text(job_id)
        
        if not extracted_text:
            print(f"No text extracted from job: {job_id}")
            update_file_status(project_id, file_id, 'textract_completed_no_text')
            return
        
        # Store extracted text in S3
        text_s3_key = f"projects/{project_id}/extracted-text/{file_id}.txt"
        store_extracted_text(text_s3_key, extracted_text)
        
        # Update file status in DynamoDB
        update_file_status(
            project_id=project_id,
            file_id=file_id,
            status='textract_completed',
            extracted_text_s3_key=text_s3_key,
            extracted_text_length=len(extracted_text)
        )
        
        # Send message to Review Agent queue (if configured)
        if REVIEW_AGENT_QUEUE_URL:
            send_to_review_agent(project_id, file_id, text_s3_key, extracted_text)
        
        print(f"Successfully processed Textract results for file: {file_id}")
        
    except Exception as e:
        print(f"Error processing Textract results: {str(e)}")
        raise


def retrieve_textract_text(job_id: str) -> str:
    """
    Retrieve all text from Textract job results.
    Handles pagination for large documents.
    
    Args:
        job_id: Textract job ID
        
    Returns:
        Extracted text as string
    """
    text_blocks = []
    next_token = None
    
    try:
        while True:
            # Get document text detection results
            params = {'JobId': job_id}
            if next_token:
                params['NextToken'] = next_token
            
            response = textract.get_document_text_detection(**params)
            
            # Extract text blocks
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block.get('Text', ''))
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        # Join all text blocks with newlines
        extracted_text = '\n'.join(text_blocks)
        
        print(f"Extracted {len(text_blocks)} text lines, total length: {len(extracted_text)}")
        
        return extracted_text
        
    except ClientError as e:
        print(f"Error retrieving Textract results: {str(e)}")
        raise


def store_extracted_text(s3_key: str, text: str):
    """
    Store extracted text in S3.
    
    Args:
        s3_key: S3 object key
        text: Extracted text content
    """
    try:
        s3.put_object(
            Bucket=EXTRACTED_TEXT_BUCKET,
            Key=s3_key,
            Body=text.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'extraction_source': 'textract',
                'extraction_timestamp': get_timestamp()
            }
        )
        
        print(f"Stored extracted text at: s3://{EXTRACTED_TEXT_BUCKET}/{s3_key}")
        
    except ClientError as e:
        print(f"Error storing extracted text: {str(e)}")
        raise


def send_to_review_agent(project_id: str, file_id: str, text_s3_key: str, extracted_text: str):
    """
    Send extracted text to Review Agent queue for processing.
    
    Args:
        project_id: Project identifier
        file_id: File identifier
        text_s3_key: S3 key where text is stored
        extracted_text: Extracted text content
    """
    try:
        message = {
            'event_type': 'document_extracted',
            'project_id': project_id,
            'file_id': file_id,
            'text_s3_key': text_s3_key,
            'text_length': len(extracted_text),
            'timestamp': get_timestamp()
        }
        
        # Include text directly if it's small enough (< 256KB SQS limit)
        if len(extracted_text) < 200000:  # Leave buffer for JSON overhead
            message['extracted_text'] = extracted_text
        
        sqs.send_message(
            QueueUrl=REVIEW_AGENT_QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        
        print(f"Sent message to Review Agent queue for file: {file_id}")
        
    except ClientError as e:
        print(f"Error sending to Review Agent queue: {str(e)}")
        # Don't raise - text is already stored in S3


def handle_textract_failure(job_id: str, message: dict):
    """
    Handle Textract job failure.
    
    Args:
        job_id: Textract job ID
        message: SNS message with failure details
    """
    try:
        # Get file information
        file_info = get_file_by_job_id(job_id)
        if not file_info:
            print(f"File not found for failed job: {job_id}")
            return
        
        project_id = file_info['project_id']
        file_id = file_info['file_id']
        
        error_message = message.get('StatusMessage', 'Unknown error')
        
        print(f"Textract job failed for file {file_id}: {error_message}")
        
        # Update file status
        update_file_status(
            project_id=project_id,
            file_id=file_id,
            status='textract_failed',
            error_message=error_message
        )
        
    except Exception as e:
        print(f"Error handling Textract failure: {str(e)}")


def get_file_by_job_id(job_id: str) -> dict:
    """
    Find file information by Textract job ID.
    
    Args:
        job_id: Textract job ID
        
    Returns:
        File information dict or None
    """
    try:
        # Query DynamoDB for file with this job_id
        # Note: This requires a GSI on textract_job_id or a scan
        # For now, we'll use the job tag which should be the file_id
        
        # The job tag was set to file_id in the trigger lambda
        # We need to scan or use a GSI to find the file
        # For simplicity, we'll assume the job tag is the file_id
        
        # This is a simplified approach - in production, you'd want a GSI
        response = dynamodb.scan(
            TableName=DYNAMODB_TABLE_NAME,
            FilterExpression='textract_job_id = :job_id',
            ExpressionAttributeValues={
                ':job_id': {'S': job_id}
            },
            Limit=1
        )
        
        if response.get('Items'):
            item = response['Items'][0]
            return {
                'project_id': item['project_id']['S'],
                'file_id': item['file_id']['S']
            }
        
        return None
        
    except ClientError as e:
        print(f"Error querying DynamoDB: {str(e)}")
        return None


def update_file_status(
    project_id: str,
    file_id: str,
    status: str,
    extracted_text_s3_key: str = None,
    extracted_text_length: int = None,
    error_message: str = None
):
    """
    Update file processing status in DynamoDB.
    
    Args:
        project_id: Project identifier
        file_id: File identifier
        status: Processing status
        extracted_text_s3_key: S3 key for extracted text (optional)
        extracted_text_length: Length of extracted text (optional)
        error_message: Error message (optional)
    """
    try:
        update_expression = "SET processing_status = :status, updated_at = :updated_at"
        expression_values = {
            ':status': {'S': status},
            ':updated_at': {'S': get_timestamp()}
        }
        
        if extracted_text_s3_key:
            update_expression += ", extracted_text_s3_key = :text_key"
            expression_values[':text_key'] = {'S': extracted_text_s3_key}
        
        if extracted_text_length is not None:
            update_expression += ", extracted_text_length = :text_length"
            expression_values[':text_length'] = {'N': str(extracted_text_length)}
        
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
