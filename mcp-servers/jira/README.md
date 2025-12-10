# Jira MCP Server

Model Context Protocol server providing CRUD operations for Jira issues.

## Features

- **create_issue**: Create new Jira issues
- **update_issue**: Update existing issues
- **delete_issue**: Delete issues
- **get_issue**: Retrieve issue details
- **search_issues**: Search issues using JQL
- Automatic retry logic with exponential backoff for rate limiting
- Comprehensive error handling
- JSON structured logging

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Jira credentials
```

3. Run the server:
```bash
python main.py
```

The server will start on `http://localhost:8001`

### Docker

Build and run with Docker:

```bash
docker build -t jira-mcp-server .
docker run -p 8001:8001 --env-file .env jira-mcp-server
```

## Configuration

Environment variables (see `.env.example`):

- `JIRA_URL`: Jira instance URL (e.g., https://your-domain.atlassian.net)
- `JIRA_API_TOKEN`: Jira API token
- `JIRA_EMAIL`: Email associated with Jira account
- `AWS_REGION`: AWS region for logging (default: us-east-1)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: development)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)
- `MAX_RETRIES`: Max retry attempts (default: 3)
- `RETRY_BACKOFF_FACTOR`: Backoff multiplier (default: 2.0)

### Getting Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label and copy the token
4. Use your email and token for authentication

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "jira-mcp-server",
  "jira_url": "https://your-domain.atlassian.net",
  "configured": true
}
```

### Create Issue

```bash
POST /tools/create_issue
Content-Type: application/json

{
  "project_key": "MED",
  "issue_type": "Epic",
  "summary": "User Authentication",
  "description": "Implement user authentication features",
  "fields": {
    "priority": {"name": "High"},
    "labels": ["security", "authentication"]
  }
}
```

Response:
```json
{
  "success": true,
  "issue_key": "MED-123",
  "issue_id": "10001",
  "issue_url": "https://your-domain.atlassian.net/browse/MED-123"
}
```

### Update Issue

```bash
POST /tools/update_issue
Content-Type: application/json

{
  "issue_key": "MED-123",
  "fields": {
    "summary": "Updated User Authentication",
    "description": "Updated description",
    "status": {"name": "In Progress"}
  }
}
```

### Delete Issue

```bash
POST /tools/delete_issue
Content-Type: application/json

{
  "issue_key": "MED-123"
}
```

### Get Issue

```bash
POST /tools/get_issue
Content-Type: application/json

{
  "issue_key": "MED-123"
}
```

Response:
```json
{
  "success": true,
  "issue_key": "MED-123",
  "issue_id": "10001",
  "issue_url": "https://your-domain.atlassian.net/browse/MED-123",
  "summary": "User Authentication",
  "description": "Implement user authentication features",
  "status": "Open",
  "issue_type": "Epic",
  "project": "MED"
}
```

### Search Issues

```bash
POST /tools/search_issues
Content-Type: application/json

{
  "jql_query": "project = MED AND status = Open",
  "max_results": 50,
  "start_at": 0
}
```

Response:
```json
{
  "success": true,
  "issues": [
    {
      "issue_key": "MED-123",
      "issue_id": "10001",
      "issue_url": "https://your-domain.atlassian.net/browse/MED-123",
      "summary": "User Authentication",
      "status": "Open",
      "issue_type": "Epic"
    }
  ],
  "total": 1
}
```

## Issue Types

Common Jira issue types:
- **Epic**: Large body of work
- **Story**: User story
- **Task**: Task to be done
- **Bug**: Bug to be fixed
- **Sub-task**: Sub-task of another issue

## JQL Examples

JQL (Jira Query Language) examples for searching:

```
# All issues in a project
project = MED

# Open issues
project = MED AND status = Open

# Issues assigned to you
project = MED AND assignee = currentUser()

# Issues created this week
project = MED AND created >= startOfWeek()

# High priority bugs
project = MED AND issuetype = Bug AND priority = High

# Issues with specific label
project = MED AND labels = authentication
```

## Error Handling

The server implements comprehensive error handling:

- **Rate Limiting (429)**: Automatic retry with exponential backoff
- **Authentication Errors**: Invalid credentials or expired tokens
- **Invalid Project**: Project key doesn't exist
- **Missing Fields**: Required fields not provided
- **Permission Errors**: User doesn't have permission

Error responses:
```json
{
  "success": false,
  "error": "Error message description"
}
```

## Retry Logic

The server automatically retries failed requests with exponential backoff:

- Initial retry: 2 seconds
- Second retry: 4 seconds
- Third retry: 8 seconds
- Max retries: 3 (configurable)

This handles transient failures and rate limiting gracefully.

## Testing

Run tests:
```bash
pytest tests/ -v
```

## Monitoring

The server logs all operations in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "logger": "jira-mcp",
  "service": "jira-mcp-server",
  "environment": "development",
  "message": "Issue created: MED-123"
}
```

## Common Use Cases

### Creating Test Artifacts

```python
# Create Epic
create_issue(
    project_key="MED",
    issue_type="Epic",
    summary="User Authentication & Access Control",
    description="Handles user login, authentication, and access management"
)

# Create Feature under Epic
create_issue(
    project_key="MED",
    issue_type="Story",
    summary="Login Validation",
    description="Handles user login processes",
    fields={"parent": {"key": "MED-1"}}  # Link to epic
)

# Create Test Case
create_issue(
    project_key="MED",
    issue_type="Task",
    summary="TC001: Valid User Login",
    description="Test steps:\n1. Navigate to login\n2. Enter credentials\n3. Click login",
    fields={
        "labels": ["test-case", "authentication"],
        "priority": {"name": "High"}
    }
)
```

### Updating with Compliance Tags

```python
update_issue(
    issue_key="MED-123",
    fields={
        "labels": ["FDA-820.30(g)", "IEC-62304:5.1", "ISO-13485:7.3"]
    }
)
```

### Searching for Test Cases

```python
search_issues(
    jql_query="project = MED AND labels = test-case AND status = Open",
    max_results=100
)
```

## Deployment

### ECS Fargate

1. Build and push Docker image to ECR
2. Create ECS task definition
3. Deploy to ECS Fargate cluster
4. Configure Application Load Balancer
5. Set up auto-scaling policies

See `infrastructure/` directory for IaC templates.

## Security

- Use API tokens, not passwords
- Store credentials in environment variables or AWS Secrets Manager
- Use IAM roles for ECS tasks
- Enable HTTPS for all connections
- Rotate API tokens regularly
- Implement least privilege access

## Performance

- Automatic retry with exponential backoff
- Connection pooling via jira-python library
- Configurable rate limiting
- Pagination support for large result sets

## Troubleshooting

### Authentication Issues
- Verify Jira URL is correct (include https://)
- Check API token is valid and not expired
- Ensure email matches the token owner
- Verify user has necessary permissions

### Rate Limiting
- Server automatically retries with backoff
- Consider reducing request frequency
- Check Jira rate limits for your plan

### Invalid Project Key
- Verify project exists in Jira
- Check user has access to the project
- Ensure project key is uppercase

### Missing Fields
- Check required fields for issue type
- Use Jira UI to see what fields are required
- Some fields may be required by project configuration

## Support

For issues or questions, refer to:
- [Project README](../../README.md)
- [Design Document](../../.kiro/specs/medassure-ai-platform/design.md)
- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
