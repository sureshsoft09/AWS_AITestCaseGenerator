# DynamoDB Tools Implementation Summary

## Overview
Created a comprehensive DynamoDB tools module (`dynamodb_tools.py`) to store and retrieve hierarchical test artifacts (Epics → Features → Use Cases → Test Cases) in DynamoDB table `MedAssureAI_Artifacts`.

## Files Created/Modified

### 1. `agents/dynamodb_tools.py` (NEW)
Complete DynamoDB integration with the following capabilities:

#### Key Classes
- **DynamoDBTools**: Main class handling all DynamoDB operations

#### Core Functions
1. **store_test_artifacts()**: Stores complete hierarchy of test artifacts
   - Project metadata with artifact counts
   - Epics with all nested structures
   - Jira integration fields (issue_id, issue_key, issue_url, status)
   - Compliance mappings at all levels
   - Automatic artifact counting

2. **get_project_artifacts()**: Retrieves all artifacts for a project
   - Query by project_id
   - Returns metadata and artifact structure

3. **update_jira_status()**: Updates Jira status after pushing to Jira
   - Links artifacts to Jira issues
   - Tracks push status

#### Tool Functions (for Agent Integration)
1. **store_test_artifacts_tool()**
   - Agent-callable function
   - Parameters: project_id, project_name, session_id, epics_json, jira_project_key, notification_email
   - Returns: JSON string with operation result and artifact counts

2. **get_project_artifacts_tool()**
   - Agent-callable function
   - Parameters: project_id
   - Returns: JSON string with project artifacts

#### Data Structure
```
PROJECT#{project_id}#METADATA                                    → Project metadata
PROJECT#{project_id}#EPIC#{epic_id}                             → Epic
PROJECT#{project_id}#EPIC#{epic_id}#FEATURE#{feature_id}        → Feature
PROJECT#{project_id}#EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}  → Use Case
PROJECT#{project_id}#EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}#TC#{test_case_id}  → Test Case
```

#### Stored Fields Per Artifact Type

**Epic:**
- epic_id, epic_name, description, priority
- jira_issue_id, jira_issue_key, jira_issue_url, jira_status
- created_at, updated_at

**Feature:**
- feature_id, feature_name, description, priority, epic_id
- jira_issue_id, jira_issue_key, jira_issue_url, jira_status
- created_at, updated_at

**Use Case:**
- use_case_id, title, description, priority
- epic_id, feature_id
- acceptance_criteria (list), test_scenarios_outline (list)
- compliance_mapping (list)
- model_explanation, review_status, comments
- jira_issue_id, jira_issue_key, jira_issue_url, jira_status
- created_at, updated_at

**Test Case:**
- test_case_id, test_case_title, test_type, priority
- epic_id, feature_id, use_case_id
- preconditions (list), test_steps (list)
- expected_result
- compliance_mapping (list)
- model_explanation, review_status, comments
- jira_issue_id, jira_issue_key, jira_issue_url, jira_status
- created_at, updated_at

### 2. `agents/orchestrator_agent.py` (MODIFIED)
Added DynamoDB tools integration:

#### Changes Made:
1. **Import Statement** (Line ~32):
   ```python
   from agents.dynamodb_tools import store_test_artifacts_tool, get_project_artifacts_tool
   ```

2. **System Prompt Update** (Lines ~80-90):
   Added DynamoDB storage instructions:
   ```
   **DynamoDB Storage:**
   After pushing artifacts to Jira, AUTOMATICALLY store all test artifacts in DynamoDB:
   - Use store_test_artifacts_tool to save epics, features, use cases, and test cases
   - Include project_id, project_name, session_id, and the complete epics structure
   ```

3. **Tools List** (Line ~365):
   ```python
   tools_list = [
       reviewer_agenttool,
       testgenerator_agenttool,
       enhance_agenttool,
       migrate_agenttool,
       mem0_memory,
       store_test_artifacts_tool,      # NEW
       get_project_artifacts_tool       # NEW
   ]
   ```

### 3. `agents/test_dynamodb_tools.py` (NEW)
Test script to verify DynamoDB tools functionality:
- Tests storing sample test artifacts
- Tests retrieving stored artifacts
- Validates artifact counts
- Provides visual feedback on success/failure

### 4. `agents/.env` (ALREADY CONFIGURED)
DynamoDB configuration already present:
```
DYNAMODB_TABLE_NAME=MedAssureAI_Artifacts
```

## Integration Workflow

### Agent Execution Flow:
1. **Requirement Review** → reviewer_agent analyzes requirements
2. **Test Generation** → test_generator_agent creates artifacts
3. **Jira Push** → Jira MCP tools create issues in Jira
4. **DynamoDB Storage** → DynamoDB tools store artifacts with Jira references
5. **Status Update** → Update Jira status in stored artifacts

### Example Agent Call:
```python
# After test generation, the agent will automatically call:
store_test_artifacts_tool(
    project_id="healthcare_app_001",
    project_name="Healthcare Management System",
    session_id="session_abc123",
    epics_json='[{"epic_id": "E001", "epic_name": "Authentication", ...}]',
    jira_project_key="HS25SKL",
    notification_email="user@example.com"
)
```

### Response Format:
```json
{
  "success": true,
  "project_id": "healthcare_app_001",
  "project_name": "Healthcare Management System",
  "artifact_counts": {
    "epics": 1,
    "features": 1,
    "use_cases": 1,
    "test_cases": 2
  },
  "stored_at": "2025-12-11T10:30:00.000Z",
  "message": "Successfully stored 2 test cases across 1 epics"
}
```

## Testing

### Run Test Suite:
```bash
cd "d:\Sample Projects\AWS Samples\Kiro Projects\MedAssureAI"
python -m agents.test_dynamodb_tools
```

### Expected Output:
```
================================================================================
DynamoDB Tools Test Suite
================================================================================

Testing store_test_artifacts_tool...
--------------------------------------------------------------------------------
Store Result:
{
  "success": true,
  "project_id": "test_project_001",
  ...
}
--------------------------------------------------------------------------------
✓ Successfully stored test artifacts!
  - Epics: 1
  - Features: 1
  - Use Cases: 1
  - Test Cases: 2

Testing get_project_artifacts_tool...
--------------------------------------------------------------------------------
...
✓ Successfully retrieved project artifacts!
  Project: Test Healthcare Application
  Session: test_session_123
```

## Benefits

1. **Hierarchical Storage**: Maintains parent-child relationships between artifacts
2. **Jira Integration**: Tracks Jira push status and issue references
3. **Compliance Tracking**: Stores compliance mappings (FDA, ISO, IEC)
4. **Audit Trail**: Timestamps for creation and updates
5. **Query Efficiency**: Optimized for querying by project_id
6. **Agent Integration**: Seamlessly integrated into orchestrator workflow
7. **Error Handling**: Comprehensive error handling with detailed logging

## DynamoDB Table Structure

### Primary Key:
- **PK (Partition Key)**: `PROJECT#{project_id}`
- **SK (Sort Key)**: Hierarchical identifier (METADATA, EPIC#..., FEATURE#..., etc.)

### Access Patterns:
1. Get all artifacts for a project: Query by PK
2. Get specific artifact: Query by PK + SK
3. Get all epics: Query by PK, SK begins_with "EPIC#"
4. Get all features in epic: Query by PK, SK begins_with "EPIC#{epic_id}#FEATURE#"

## Next Steps

1. **Test with Real Data**: Run test script to verify AWS credentials and table access
2. **Backend Integration**: Update backend to call agent with proper session tracking
3. **Jira Integration**: Ensure Jira MCP tools update DynamoDB after creating issues
4. **Dashboard Integration**: Create queries to display artifacts in dashboard
5. **Monitoring**: Add CloudWatch metrics for storage operations

## Configuration Requirements

Ensure these environment variables are set in `agents/.env`:
- `AWS_REGION`: AWS region (default: us-east-1)
- `DYNAMODB_TABLE_NAME`: MedAssureAI_Artifacts
- AWS credentials configured (via ~/.aws/credentials or environment variables)

## Error Handling

The tools include comprehensive error handling for:
- Invalid JSON format in epics_json
- DynamoDB ClientError (permissions, table not found, etc.)
- Missing required fields
- Network/connection issues

All errors are logged with context and returned as JSON responses with success=false.
