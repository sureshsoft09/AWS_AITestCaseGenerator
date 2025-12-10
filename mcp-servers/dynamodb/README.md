# DynamoDB MCP Server

Model Context Protocol server providing CRUD operations for DynamoDB.

## Features

- **put_item**: Store items in DynamoDB
- **get_item**: Retrieve items by primary key
- **update_item**: Update existing items
- **delete_item**: Delete items
- **query**: Query table or GSI with key conditions
- **scan**: Scan table with optional filters
- Connection pooling for efficient resource usage
- Automatic retry logic for throttling
- Pagination support for large result sets
- Comprehensive error handling and logging

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your AWS credentials and configuration
```

3. Run the server:
```bash
python main.py
```

The server will start on `http://localhost:8002`

### Docker

Build and run with Docker:

```bash
docker build -t dynamodb-mcp-server .
docker run -p 8002:8002 --env-file .env dynamodb-mcp-server
```

## Configuration

Environment variables (see `.env.example`):

- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `DYNAMODB_TABLE_NAME`: Table name (default: MedAssureAI_Artifacts)
- `DYNAMODB_ENDPOINT_URL`: For local DynamoDB (optional)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: development)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8002)

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "dynamodb-mcp-server",
  "table": "MedAssureAI_Artifacts"
}
```

### Put Item

```bash
POST /tools/put_item
Content-Type: application/json

{
  "item": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E001",
    "epic_name": "User Authentication",
    "description": "Authentication features"
  }
}
```

### Get Item

```bash
POST /tools/get_item
Content-Type: application/json

{
  "key": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E001"
  }
}
```

### Update Item

```bash
POST /tools/update_item
Content-Type: application/json

{
  "key": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E001"
  },
  "updates": {
    "jira_issue_key": "MED-123",
    "jira_status": "Open"
  }
}
```

### Delete Item

```bash
POST /tools/delete_item
Content-Type: application/json

{
  "key": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E001"
  }
}
```

### Query

```bash
POST /tools/query
Content-Type: application/json

{
  "key_condition": "PK = :pk",
  "expression_values": {
    ":pk": "PROJECT#test123"
  },
  "limit": 100
}
```

Query with GSI:
```bash
POST /tools/query
Content-Type: application/json

{
  "key_condition": "GSI1PK = :gsi1pk",
  "expression_values": {
    ":gsi1pk": "EPIC#E001"
  },
  "index_name": "GSI1"
}
```

### Scan

```bash
POST /tools/scan
Content-Type: application/json

{
  "filter_expression": "entity_type = :type",
  "expression_values": {
    ":type": "project"
  },
  "limit": 50
}
```

## Error Handling

The server implements comprehensive error handling:

- **ClientError**: DynamoDB client errors (throttling, validation, etc.)
- **BotoCoreError**: AWS SDK errors
- **Retry Logic**: Automatic retries with exponential backoff for throttling
- **Logging**: All errors logged with context for debugging

Error responses include:
```json
{
  "success": false,
  "error": "Error message description"
}
```

## Pagination

For queries and scans that return many items, use pagination:

```bash
POST /tools/query
Content-Type: application/json

{
  "key_condition": "PK = :pk",
  "expression_values": {
    ":pk": "PROJECT#test123"
  },
  "limit": 10,
  "last_evaluated_key": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E010"
  }
}
```

Response includes `last_evaluated_key` for next page:
```json
{
  "success": true,
  "items": [...],
  "count": 10,
  "last_evaluated_key": {
    "PK": "PROJECT#test123",
    "SK": "EPIC#E020"
  }
}
```

## Testing

Run tests:
```bash
pytest tests/ -v
```

## Monitoring

The server logs all operations in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "logger": "dynamodb-mcp",
  "service": "dynamodb-mcp-server",
  "environment": "development",
  "message": "Item stored successfully: PK=PROJECT#test123, SK=EPIC#E001"
}
```

## Local DynamoDB

For local development, use DynamoDB Local:

```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

Set `DYNAMODB_ENDPOINT_URL=http://localhost:8000` in your `.env` file.

## Deployment

### ECS Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy to ECS Fargate cluster
4. Configure Application Load Balancer
5. Set up auto-scaling policies

See `infrastructure/` directory for IaC templates.

## Security

- Use IAM roles for ECS tasks (don't hardcode credentials)
- Enable encryption at rest in DynamoDB
- Use VPC endpoints for private access
- Implement least privilege IAM policies
- Enable CloudWatch logging for audit

## Performance

- Connection pooling enabled by default
- Batch operations supported via client
- Pagination for large result sets
- Automatic retry with exponential backoff
- On-demand billing mode for variable workloads

## Troubleshooting

### Connection Issues
- Verify AWS credentials are correct
- Check network connectivity to DynamoDB
- Ensure IAM permissions are sufficient

### Throttling
- Monitor CloudWatch metrics for throttle events
- Consider provisioned capacity for predictable workloads
- Implement exponential backoff (already included)

### Performance
- Use query instead of scan when possible
- Implement pagination for large datasets
- Monitor DynamoDB capacity metrics
- Consider caching frequently accessed data

## Support

For issues or questions, refer to:
- [DynamoDB Schema Documentation](../../infrastructure/DYNAMODB_SCHEMA.md)
- [Project README](../../README.md)
- [Design Document](../../.kiro/specs/medassure-ai-platform/design.md)
