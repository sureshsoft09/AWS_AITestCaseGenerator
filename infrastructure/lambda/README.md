# MedAssureAI Lambda Functions

This directory contains AWS Lambda functions for the MedAssureAI document processing pipeline.

## Lambda Functions

### 1. Textract Trigger (`textract-trigger/`)

**Purpose**: Triggered by S3 object creation events to initiate Textract document text detection.

**Trigger**: S3 Event Notification (ObjectCreated)

**Key Features**:
- Validates document type (PDF, images)
- Starts Textract document text detection job
- Updates file processing status in DynamoDB
- Configures SNS notifications for job completion

**Environment Variables**:
- `SNS_TOPIC_ARN`: ARN of SNS topic for Textract completion notifications
- `SNS_ROLE_ARN`: ARN of IAM role for Textract to publish to SNS
- `DYNAMODB_TABLE_NAME`: Name of DynamoDB table for metadata storage

### 2. Textract Completion (`textract-completion/`)

**Purpose**: Handles Textract job completion notifications and retrieves extracted text.

**Trigger**: SNS Topic Subscription (Textract completion notifications)

**Key Features**:
- Retrieves extracted text from completed Textract jobs
- Handles pagination for large documents
- Stores extracted text in S3
- Updates file processing status in DynamoDB
- Sends extracted text to Review Agent queue (optional)

**Environment Variables**:
- `EXTRACTED_TEXT_BUCKET`: S3 bucket for storing extracted text
- `REVIEW_AGENT_QUEUE_URL`: SQS queue URL for Review Agent
- `DYNAMODB_TABLE_NAME`: Name of DynamoDB table for metadata storage

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. CloudFormation stack deployed (`textract-pipeline.yaml`)
3. S3 buckets created (ingest bucket, extracted text bucket)
4. DynamoDB table created

### Deploy Infrastructure

```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file ../cloudformation/textract-pipeline.yaml \
  --stack-name medassure-textract-pipeline \
  --parameter-overrides \
    Environment=development \
    IngestBucketName=medassure-ingest-bucket \
    ExtractedTextBucketName=medassure-extracted-text-bucket \
    DynamoDBTableName=MedAssureAI_Artifacts \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Deploy Lambda Functions

```bash
# Make deployment script executable
chmod +x deploy-lambdas.sh

# Deploy to development environment
./deploy-lambdas.sh development

# Deploy to production environment
./deploy-lambdas.sh production
```

### Configure S3 Event Notification

After deploying the Lambda functions, configure the S3 ingest bucket to trigger the Textract Trigger Lambda:

```bash
# Get Lambda function ARN
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name medassure-textract-pipeline \
  --query 'Stacks[0].Outputs[?OutputKey==`TextractTriggerFunctionArn`].OutputValue' \
  --output text)

# Configure S3 event notification
aws s3api put-bucket-notification-configuration \
  --bucket medassure-ingest-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "'$LAMBDA_ARN'",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "prefix",
                "Value": "projects/"
              }
            ]
          }
        }
      }
    ]
  }'
```

## Testing

### Test Textract Trigger Lambda

```bash
# Upload a test document to S3
aws s3 cp test-document.pdf s3://medassure-ingest-bucket/projects/test_project/documents/test-file-id/test-document.pdf

# Check CloudWatch Logs
aws logs tail /aws/lambda/development-medassure-textract-trigger --follow
```

### Test Textract Completion Lambda

The completion Lambda is automatically triggered by SNS when Textract jobs complete. Monitor CloudWatch Logs:

```bash
aws logs tail /aws/lambda/development-medassure-textract-completion --follow
```

## Monitoring

### CloudWatch Metrics

- Lambda invocations
- Lambda errors
- Lambda duration
- Textract job success/failure rates

### CloudWatch Logs

- `/aws/lambda/development-medassure-textract-trigger`
- `/aws/lambda/development-medassure-textract-completion`

### Alarms

Set up CloudWatch alarms for:
- Lambda error rate > 5%
- Lambda throttling
- Textract job failures
- SQS queue depth (Review Agent queue)

## Architecture Flow

```
1. User uploads document → S3 Ingest Bucket
2. S3 Event → Textract Trigger Lambda
3. Lambda → Start Textract Job (with SNS notification)
4. Textract Job Completes → SNS Topic
5. SNS → Textract Completion Lambda
6. Lambda → Retrieve extracted text
7. Lambda → Store text in S3
8. Lambda → Update DynamoDB
9. Lambda → Send to Review Agent Queue (optional)
```

## Error Handling

### Textract Trigger Lambda

- Invalid file format: Updates status to `unsupported_format`
- Textract API error: Updates status to `textract_failed` with error message
- DynamoDB update failure: Logged but doesn't fail the request

### Textract Completion Lambda

- Job failure: Updates status to `textract_failed`
- No text extracted: Updates status to `textract_completed_no_text`
- S3 storage failure: Raises exception (text retrieval is critical)
- SQS send failure: Logged but doesn't fail (text is already in S3)

## Cost Optimization

- Use Textract only for supported document types
- Store extracted text in S3 Standard-IA after 30 days
- Set SQS message retention to 14 days
- Use Lambda reserved concurrency to control costs
- Monitor Textract usage and optimize document sizes

## Security

- Lambda functions use IAM roles with least privilege
- S3 buckets have encryption at rest enabled
- SNS topics have access policies restricting publishers
- DynamoDB table has encryption enabled
- CloudWatch Logs are retained for compliance

## Troubleshooting

### Lambda not triggered by S3

- Check S3 event notification configuration
- Verify Lambda permission for S3 to invoke
- Check S3 object key matches filter prefix

### Textract job fails

- Check document format and size limits
- Verify IAM role has Textract permissions
- Check CloudWatch Logs for error details

### Text not stored in S3

- Verify Lambda has S3 PutObject permission
- Check S3 bucket exists and is accessible
- Review CloudWatch Logs for errors

### Review Agent not receiving messages

- Verify SQS queue URL is correct
- Check Lambda has SQS SendMessage permission
- Monitor SQS queue metrics in CloudWatch
