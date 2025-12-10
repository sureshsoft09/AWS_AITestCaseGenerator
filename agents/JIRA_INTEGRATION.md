# Jira MCP Integration Guide

## Overview

The MedAssureAI orchestrator agent is integrated with a Jira MCP (Model Context Protocol) server to automatically push generated test artifacts to Jira.

## Architecture

```
┌─────────────────────┐
│ Orchestrator Agent  │
│   (Port 8001)      │
└──────────┬──────────┘
           │
           │ MCP Client
           ▼
┌─────────────────────┐
│  Jira MCP Server   │
│   (Port 8084)      │
└──────────┬──────────┘
           │
           │ Jira REST API
           ▼
┌─────────────────────┐
│  Jira Cloud        │
│  (hsskill.atlassian)│
└─────────────────────┘
```

## Configuration

### Environment Variables

**agents/.env**
```env
JIRA_MCP_SERVER_URL=http://localhost:8084/mcp
JIRA_PROJECT_KEY=HS25SKL
```

**mcp-servers/jira/.env**
```env
JIRA_URL=https://hsskill.atlassian.net
JIRA_API_TOKEN=<your-api-token>
JIRA_EMAIL=<your-email>
PORT=8084
```

## Artifact to Issue Type Mapping

The orchestrator automatically maps test artifacts to Jira issue types:

| Artifact Type | Jira Issue Type |
|---------------|-----------------|
| Epic          | Epic            |
| Feature       | New Feature     |
| Use Case      | Improvement     |
| Test Case     | Task            |

## Available Jira MCP Tools

The orchestrator has access to the following Jira tools:

1. **create_issue** - Create a single Jira issue
   - Parameters:
     - `project_key`: Jira project key (e.g., 'HS25SKL')
     - `issue_type`: Issue type ('Epic', 'New Feature', 'Improvement', 'Task')
     - `summary`: Issue summary/title
     - `description`: Issue description
     - `fields`: Optional additional fields

2. **create_issues_batch** - Create multiple Jira issues in batch
   - Parameters:
     - `jira_issues`: List of issue dictionaries
     - `project_key`: Jira project key

3. **update_issue** - Update an existing issue
4. **delete_issue** - Delete an issue
5. **get_issue** - Retrieve issue details
6. **search_issues** - Search using JQL queries

## Workflow

1. **User Request**: User asks to generate test artifacts
   ```
   "Generate test cases for Patient Information Collection feature"
   ```

2. **Agent Processing**:
   - Orchestrator delegates to Test Generator Agent
   - Test Generator creates artifacts (Epic, Feature, Use Cases, Test Cases)
   - Returns structured artifact data

3. **Automatic Jira Integration**:
   - Orchestrator detects generated artifacts
   - Maps each artifact to appropriate Jira issue type
   - Calls `create_issue` for each artifact
   - Creates parent-child relationships (Epic → Feature → Use Case → Test Case)

4. **Response to User**:
   ```json
   {
     "artifacts_generated": 15,
     "jira_issues_created": [
       {
         "type": "Epic",
         "key": "HS25SKL-123",
         "url": "https://hsskill.atlassian.net/browse/HS25SKL-123"
       },
       {
         "type": "New Feature",
         "key": "HS25SKL-124",
         "url": "https://hsskill.atlassian.net/browse/HS25SKL-124"
       }
     ]
   }
   ```

## Starting the Services

### 1. Start Jira MCP Server

```powershell
cd "d:\Sample Projects\AWS Samples\Kiro Projects\MedAssureAI\mcp-servers\jira"
python main.py
```

Expected output:
```
INFO: Jira client initialized for: https://hsskill.atlassian.net
INFO: Starting Jira MCP Server
```

### 2. Start Orchestrator Agent

```powershell
cd "d:\Sample Projects\AWS Samples\Kiro Projects\MedAssureAI"
.venv\Scripts\python.exe -m agents.orchestrator_agent
```

Expected output:
```
INFO: Loaded 6 Jira MCP tools
INFO: MedAssureAI Agents Service starting up
INFO: Orchestrator initialized with 4 specialized agents
INFO: Uvicorn running on http://0.0.0.0:8001
```

## Testing the Integration

### Test Create Single Issue

```bash
curl -X POST http://localhost:8001/processquery \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-1",
    "user_query": "Create a Jira epic for Patient Registration System"
  }'
```

### Test Generate and Push Artifacts

```bash
curl -X POST http://localhost:8001/processquery \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-2",
    "user_query": "Generate test cases for user authentication and push to Jira"
  }'
```

## Troubleshooting

### Jira MCP Tools Not Loading

**Error**: `Failed to load Jira MCP tools: Connection refused`

**Solution**: Ensure Jira MCP server is running on port 8084
```powershell
cd mcp-servers\jira
python main.py
```

### Authentication Errors

**Error**: `401 Unauthorized`

**Solution**: Verify Jira API token and email in `mcp-servers/jira/.env`

### Port Conflicts

**Error**: `Address already in use`

**Solution**: Check if ports 8001 (orchestrator) or 8084 (Jira MCP) are already in use
```powershell
netstat -ano | findstr :8001
netstat -ano | findstr :8084
```

## Best Practices

1. **Always start Jira MCP server first** before starting the orchestrator agent
2. **Use meaningful summaries** - They become Jira issue titles
3. **Include detailed descriptions** - They appear in Jira issue descriptions
4. **Batch operations** - Use `create_issues_batch` for multiple issues to avoid rate limiting
5. **Monitor logs** - Both services log Jira API calls for debugging

## Advanced Configuration

### Custom Issue Fields

Add custom fields when creating issues:

```python
fields = {
    "priority": {"name": "High"},
    "labels": ["healthcare", "test-automation"],
    "customfield_10000": "Custom value"
}
```

### Parent-Child Relationships

Link issues hierarchically:

```python
# Create epic first
epic = create_issue(issue_type="Epic", summary="User Management")

# Link feature to epic
feature_fields = {
    "parent": {"key": epic["issue_key"]}
}
create_issue(issue_type="New Feature", fields=feature_fields)
```

## Monitoring

Monitor Jira integration activity:

1. **Agent Logs**: Check `agents/logs/` for orchestrator activity
2. **Jira MCP Logs**: Check `mcp-servers/jira/logs/` for API calls
3. **Jira Activity**: View in Jira project activity feed

## Security Notes

- API tokens are stored in `.env` files (never commit to git)
- MCP communication over HTTP localhost only (not exposed externally)
- Consider using OAuth2 for production deployments
- Implement rate limiting for high-volume operations

## Future Enhancements

- [ ] Automatic issue linking based on traceability
- [ ] Attachment support for test data files
- [ ] Jira workflow automation triggers
- [ ] Bi-directional sync (Jira → MedAssureAI)
- [ ] Custom field mapping configuration
- [ ] Bulk update operations
- [ ] Comment synchronization
