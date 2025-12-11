"""
Test script for DynamoDB Tools
Verifies that the DynamoDB tools can store and retrieve test artifacts
"""
import json
from agents.dynamodb_tools import store_test_artifacts_tool, get_project_artifacts_tool


def test_store_artifacts():
    """Test storing test artifacts in DynamoDB"""
    
    # Sample test artifacts structure
    test_epics = [
        {
            "epic_id": "E001",
            "epic_name": "User Authentication & Access Control",
            "description": "Handles user login, authentication, and access management functionalities.",
            "priority": "Critical",
            "jira_issue_id": None,
            "jira_issue_key": None,
            "jira_issue_url": None,
            "jira_status": "Not Pushed",
            "features": [
                {
                    "feature_id": "F001",
                    "feature_name": "Login Validation",
                    "description": "Handles user login processes including credential validation and session management.",
                    "priority": "High",
                    "jira_issue_id": None,
                    "jira_issue_key": None,
                    "jira_issue_url": None,
                    "jira_status": "Not Pushed",
                    "use_cases": [
                        {
                            "use_case_id": "UC001",
                            "title": "User logs in with valid credentials",
                            "description": "System validates user credentials and provides access.",
                            "acceptance_criteria": [
                                "Given valid user credentials, when the user attempts to log in, then the system should grant access and log the event in the audit trail.",
                                "Given invalid user credentials, when the user attempts to log in, then the system should deny access and log the failed attempt in the audit trail."
                            ],
                            "priority": "Medium",
                            "jira_issue_id": None,
                            "jira_issue_key": None,
                            "jira_issue_url": None,
                            "jira_status": "Not Pushed",
                            "test_scenarios_outline": [
                                "Verify login success for valid credentials",
                                "Validate error handling for invalid password",
                                "Check audit log entry after login"
                            ],
                            "model_explanation": "Derived from authentication and access control requirements validated under ISO 9001 and FDA 820.30(g).",
                            "review_status": "Approved",
                            "comments": "Use case well-defined and compliant.",
                            "test_cases": [
                                {
                                    "test_case_id": "TC001",
                                    "test_case_title": "Valid User Login",
                                    "preconditions": [
                                        "User exists in system",
                                        "Credentials are valid"
                                    ],
                                    "test_steps": [
                                        "Navigate to login page",
                                        "Enter username and password",
                                        "Click login"
                                    ],
                                    "expected_result": "System grants access and logs event in audit trail.",
                                    "test_type": "Functional",
                                    "priority": "High",
                                    "jira_issue_id": None,
                                    "jira_issue_key": None,
                                    "jira_issue_url": None,
                                    "jira_status": "Not Pushed",
                                    "compliance_mapping": [
                                        "FDA 820.30(g)",
                                        "IEC 62304:5.1",
                                        "ISO 13485:7.3",
                                        "ISO 9001:8.5"
                                    ],
                                    "model_explanation": "Derived from validated requirement-to-test linkage under ISO and FDA frameworks.",
                                    "review_status": "Approved",
                                    "comments": "Test case meets all compliance and explainability criteria."
                                },
                                {
                                    "test_case_id": "TC002",
                                    "test_case_title": "Invalid Password Login Attempt",
                                    "preconditions": [
                                        "User exists in system"
                                    ],
                                    "test_steps": [
                                        "Enter incorrect password",
                                        "Click login"
                                    ],
                                    "expected_result": "System displays error and logs failed attempt.",
                                    "test_type": "Negative",
                                    "priority": "Low",
                                    "jira_issue_id": None,
                                    "jira_issue_key": None,
                                    "jira_issue_url": None,
                                    "jira_status": "Not Pushed",
                                    "compliance_mapping": [
                                        "FDA 820.30(g)",
                                        "IEC 62304:5.1"
                                    ],
                                    "model_explanation": "Derived from negative path validation requirements.",
                                    "review_status": "Needs Clarification",
                                    "comments": "Missing ISO 9001 mapping; clarify expected validation method."
                                }
                            ],
                            "compliance_mapping": [
                                "FDA 820.30(g)",
                                "IEC 62304:5.1",
                                "ISO 13485:7.3",
                                "ISO 9001:8.5"
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    
    # Convert to JSON string
    epics_json = json.dumps(test_epics)
    
    # Test storing artifacts
    print("Testing store_test_artifacts_tool...")
    print("-" * 80)
    
    result = store_test_artifacts_tool(
        project_id="test_project_001",
        project_name="Test Healthcare Application",
        session_id="test_session_123",
        epics_json=epics_json,
        jira_project_key="HS25SKL",
        notification_email="test@example.com"
    )
    
    print("Store Result:")
    print(result)
    print("-" * 80)
    
    # Parse result
    result_data = json.loads(result)
    
    if result_data.get('success'):
        print("✓ Successfully stored test artifacts!")
        print(f"  - Epics: {result_data['artifact_counts']['epics']}")
        print(f"  - Features: {result_data['artifact_counts']['features']}")
        print(f"  - Use Cases: {result_data['artifact_counts']['use_cases']}")
        print(f"  - Test Cases: {result_data['artifact_counts']['test_cases']}")
    else:
        print("✗ Failed to store artifacts:")
        print(f"  Error: {result_data.get('error')}")
    
    print()
    return result_data.get('success', False)


def test_retrieve_artifacts():
    """Test retrieving test artifacts from DynamoDB"""
    
    print("Testing get_project_artifacts_tool...")
    print("-" * 80)
    
    result = get_project_artifacts_tool(project_id="test_project_001")
    
    print("Retrieve Result:")
    print(result)
    print("-" * 80)
    
    # Parse result
    result_data = json.loads(result)
    
    if result_data.get('success'):
        print("✓ Successfully retrieved project artifacts!")
        if 'metadata' in result_data:
            print(f"  Project: {result_data['metadata'].get('project_name', 'N/A')}")
            print(f"  Session: {result_data['metadata'].get('session_id', 'N/A')}")
    else:
        print("✗ Failed to retrieve artifacts:")
        print(f"  Error: {result_data.get('error')}")
    
    print()


if __name__ == "__main__":
    print("=" * 80)
    print("DynamoDB Tools Test Suite")
    print("=" * 80)
    print()
    
    # Test storing artifacts
    success = test_store_artifacts()
    
    # Test retrieving artifacts (only if store was successful)
    if success:
        test_retrieve_artifacts()
    
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
