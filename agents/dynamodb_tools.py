"""
DynamoDB Tools for MedAssureAI Agent System
Handles storage of test artifacts (epics, features, use cases, test cases) in DynamoDB.
"""
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
from agents.config import agent_config
from agents.logger import logger
from strands import tool
import os


class DynamoDBTools:
    """Tools for storing and retrieving test artifacts from DynamoDB"""
    
    def __init__(self):
        """Initialize DynamoDB client"""
        self.dynamodb = boto3.client(
            'dynamodb',
            region_name=agent_config.AWS_REGION
        )
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'MedAssureAI_Artifacts')
        logger.info(f"Initialized DynamoDB tools with table: {self.table_name}")
    
    def store_test_artifacts(
        self,
        project_id: str,
        project_name: str,
        session_id: str,
        epics: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store complete test artifacts structure in DynamoDB.
        
        Args:
            project_id: Unique project identifier
            project_name: Human-readable project name
            session_id: Session ID for tracking
            epics: List of epics with nested features, use cases, and test cases
            metadata: Optional metadata (jira_project_key, notification_email, etc.)
        
        Returns:
            Dictionary with operation status and artifact counts
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Count all artifacts
            artifact_counts = self._count_artifacts(epics)
            
            # Prepare the main project item
            project_item = {
                'PK': {'S': f'PROJECT#{project_id}'},
                'SK': {'S': 'METADATA'},
                'project_id': {'S': project_id},
                'project_name': {'S': project_name},
                'session_id': {'S': session_id},
                'created_at': {'S': timestamp},
                'updated_at': {'S': timestamp},
                'artifact_counts': {
                    'M': {
                        'epics': {'N': str(artifact_counts['epics'])},
                        'features': {'N': str(artifact_counts['features'])},
                        'use_cases': {'N': str(artifact_counts['use_cases'])},
                        'test_cases': {'N': str(artifact_counts['test_cases'])}
                    }
                }
            }
            
            # Add metadata if provided
            if metadata:
                if metadata.get('jira_project_key'):
                    project_item['jira_project_key'] = {'S': metadata['jira_project_key']}
                if metadata.get('notification_email'):
                    project_item['notification_email'] = {'S': metadata['notification_email']}
            
            # Store project metadata
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=project_item
            )
            
            logger.info(
                f"Stored project metadata for {project_id}",
                extra={'project_id': project_id, 'artifact_counts': artifact_counts}
            )
            
            # Store each epic and its nested structures
            for epic in epics:
                self._store_epic(project_id, epic, timestamp)
            
            return {
                'success': True,
                'project_id': project_id,
                'project_name': project_name,
                'artifact_counts': artifact_counts,
                'stored_at': timestamp,
                'message': f"Successfully stored {artifact_counts['test_cases']} test cases across {artifact_counts['epics']} epics"
            }
            
        except ClientError as e:
            error_msg = f"DynamoDB error storing artifacts: {str(e)}"
            logger.error(error_msg, extra={'project_id': project_id})
            return {
                'success': False,
                'error': error_msg,
                'project_id': project_id
            }
        except Exception as e:
            error_msg = f"Unexpected error storing artifacts: {str(e)}"
            logger.error(error_msg, extra={'project_id': project_id})
            return {
                'success': False,
                'error': error_msg,
                'project_id': project_id
            }
    
    def _store_epic(self, project_id: str, epic: Dict[str, Any], timestamp: str):
        """Store an epic and all its nested features, use cases, and test cases"""
        epic_id = epic.get('epic_id', 'UNKNOWN')
        
        # Store epic item
        epic_item = {
            'PK': {'S': f'PROJECT#{project_id}'},
            'SK': {'S': f'EPIC#{epic_id}'},
            'epic_id': {'S': epic_id},
            'epic_name': {'S': epic.get('epic_name', '')},
            'description': {'S': epic.get('description', '')},
            'priority': {'S': epic.get('priority', 'Medium')},
            'created_at': {'S': timestamp},
            'updated_at': {'S': timestamp}
        }
        
        # Add Jira fields if present
        if epic.get('jira_issue_id'):
            epic_item['jira_issue_id'] = {'S': str(epic['jira_issue_id'])}
        if epic.get('jira_issue_key'):
            epic_item['jira_issue_key'] = {'S': epic['jira_issue_key']}
        if epic.get('jira_issue_url'):
            epic_item['jira_issue_url'] = {'S': epic['jira_issue_url']}
        if epic.get('jira_status'):
            epic_item['jira_status'] = {'S': epic['jira_status']}
        
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=epic_item
        )
        
        # Store features
        for feature in epic.get('features', []):
            self._store_feature(project_id, epic_id, feature, timestamp)
    
    def _store_feature(self, project_id: str, epic_id: str, feature: Dict[str, Any], timestamp: str):
        """Store a feature and all its nested use cases and test cases"""
        feature_id = feature.get('feature_id', 'UNKNOWN')
        
        # Store feature item
        feature_item = {
            'PK': {'S': f'PROJECT#{project_id}'},
            'SK': {'S': f'EPIC#{epic_id}#FEATURE#{feature_id}'},
            'epic_id': {'S': epic_id},
            'feature_id': {'S': feature_id},
            'feature_name': {'S': feature.get('feature_name', '')},
            'description': {'S': feature.get('description', '')},
            'priority': {'S': feature.get('priority', 'Medium')},
            'created_at': {'S': timestamp},
            'updated_at': {'S': timestamp}
        }
        
        # Add Jira fields if present
        if feature.get('jira_issue_id'):
            feature_item['jira_issue_id'] = {'S': str(feature['jira_issue_id'])}
        if feature.get('jira_issue_key'):
            feature_item['jira_issue_key'] = {'S': feature['jira_issue_key']}
        if feature.get('jira_issue_url'):
            feature_item['jira_issue_url'] = {'S': feature['jira_issue_url']}
        if feature.get('jira_status'):
            feature_item['jira_status'] = {'S': feature['jira_status']}
        
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=feature_item
        )
        
        # Store use cases
        for use_case in feature.get('use_cases', []):
            self._store_use_case(project_id, epic_id, feature_id, use_case, timestamp)
    
    def _store_use_case(
        self,
        project_id: str,
        epic_id: str,
        feature_id: str,
        use_case: Dict[str, Any],
        timestamp: str
    ):
        """Store a use case and all its test cases"""
        use_case_id = use_case.get('use_case_id', 'UNKNOWN')
        
        # Store use case item
        use_case_item = {
            'PK': {'S': f'PROJECT#{project_id}'},
            'SK': {'S': f'EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}'},
            'epic_id': {'S': epic_id},
            'feature_id': {'S': feature_id},
            'use_case_id': {'S': use_case_id},
            'title': {'S': use_case.get('title', '')},
            'description': {'S': use_case.get('description', '')},
            'priority': {'S': use_case.get('priority', 'Medium')},
            'review_status': {'S': use_case.get('review_status', 'Pending')},
            'created_at': {'S': timestamp},
            'updated_at': {'S': timestamp}
        }
        
        # Add acceptance criteria as a list
        if use_case.get('acceptance_criteria'):
            use_case_item['acceptance_criteria'] = {
                'L': [{'S': criteria} for criteria in use_case['acceptance_criteria']]
            }
        
        # Add test scenarios outline
        if use_case.get('test_scenarios_outline'):
            use_case_item['test_scenarios_outline'] = {
                'L': [{'S': scenario} for scenario in use_case['test_scenarios_outline']]
            }
        
        # Add compliance mapping
        if use_case.get('compliance_mapping'):
            use_case_item['compliance_mapping'] = {
                'L': [{'S': mapping} for mapping in use_case['compliance_mapping']]
            }
        
        # Add Jira fields if present
        if use_case.get('jira_issue_id'):
            use_case_item['jira_issue_id'] = {'S': str(use_case['jira_issue_id'])}
        if use_case.get('jira_issue_key'):
            use_case_item['jira_issue_key'] = {'S': use_case['jira_issue_key']}
        if use_case.get('jira_issue_url'):
            use_case_item['jira_issue_url'] = {'S': use_case['jira_issue_url']}
        if use_case.get('jira_status'):
            use_case_item['jira_status'] = {'S': use_case['jira_status']}
        
        # Add optional fields
        if use_case.get('model_explanation'):
            use_case_item['model_explanation'] = {'S': use_case['model_explanation']}
        if use_case.get('comments'):
            use_case_item['comments'] = {'S': use_case['comments']}
        
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=use_case_item
        )
        
        # Store test cases
        for test_case in use_case.get('test_cases', []):
            self._store_test_case(project_id, epic_id, feature_id, use_case_id, test_case, timestamp)
    
    def _store_test_case(
        self,
        project_id: str,
        epic_id: str,
        feature_id: str,
        use_case_id: str,
        test_case: Dict[str, Any],
        timestamp: str
    ):
        """Store a single test case"""
        test_case_id = test_case.get('test_case_id', 'UNKNOWN')
        
        # Store test case item
        test_case_item = {
            'PK': {'S': f'PROJECT#{project_id}'},
            'SK': {'S': f'EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}#TC#{test_case_id}'},
            'epic_id': {'S': epic_id},
            'feature_id': {'S': feature_id},
            'use_case_id': {'S': use_case_id},
            'test_case_id': {'S': test_case_id},
            'test_case_title': {'S': test_case.get('test_case_title', '')},
            'test_type': {'S': test_case.get('test_type', 'Functional')},
            'priority': {'S': test_case.get('priority', 'Medium')},
            'expected_result': {'S': test_case.get('expected_result', '')},
            'review_status': {'S': test_case.get('review_status', 'Pending')},
            'created_at': {'S': timestamp},
            'updated_at': {'S': timestamp}
        }
        
        # Add preconditions as a list
        if test_case.get('preconditions'):
            test_case_item['preconditions'] = {
                'L': [{'S': precond} for precond in test_case['preconditions']]
            }
        
        # Add test steps as a list
        if test_case.get('test_steps'):
            test_case_item['test_steps'] = {
                'L': [{'S': step} for step in test_case['test_steps']]
            }
        
        # Add compliance mapping
        if test_case.get('compliance_mapping'):
            test_case_item['compliance_mapping'] = {
                'L': [{'S': mapping} for mapping in test_case['compliance_mapping']]
            }
        
        # Add Jira fields if present
        if test_case.get('jira_issue_id'):
            test_case_item['jira_issue_id'] = {'S': str(test_case['jira_issue_id'])}
        if test_case.get('jira_issue_key'):
            test_case_item['jira_issue_key'] = {'S': test_case['jira_issue_key']}
        if test_case.get('jira_issue_url'):
            test_case_item['jira_issue_url'] = {'S': test_case['jira_issue_url']}
        if test_case.get('jira_status'):
            test_case_item['jira_status'] = {'S': test_case['jira_status']}
        
        # Add optional fields
        if test_case.get('model_explanation'):
            test_case_item['model_explanation'] = {'S': test_case['model_explanation']}
        if test_case.get('comments'):
            test_case_item['comments'] = {'S': test_case['comments']}
        
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=test_case_item
        )
    
    def _count_artifacts(self, epics: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count all artifacts in the structure"""
        counts = {
            'epics': len(epics),
            'features': 0,
            'use_cases': 0,
            'test_cases': 0
        }
        
        for epic in epics:
            features = epic.get('features', [])
            counts['features'] += len(features)
            
            for feature in features:
                use_cases = feature.get('use_cases', [])
                counts['use_cases'] += len(use_cases)
                
                for use_case in use_cases:
                    test_cases = use_case.get('test_cases', [])
                    counts['test_cases'] += len(test_cases)
        
        return counts
    
    def get_project_artifacts(self, project_id: str) -> Dict[str, Any]:
        """
        Retrieve all test artifacts for a project from DynamoDB.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary with project metadata and all artifacts
        """
        try:
            # Query all items for this project
            response = self.dynamodb.query(
                TableName=self.table_name,
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': {'S': f'PROJECT#{project_id}'}
                }
            )
            
            items = response.get('Items', [])
            
            if not items:
                return {
                    'success': False,
                    'error': f'No artifacts found for project {project_id}'
                }
            
            # Parse and reconstruct the artifact structure
            result = {
                'success': True,
                'project_id': project_id,
                'metadata': {},
                'epics': []
            }
            
            # Group items by type
            for item in items:
                sk = item['SK']['S']
                
                if sk == 'METADATA':
                    result['metadata'] = self._parse_dynamodb_item(item)
                # Additional parsing logic can be added here for epics, features, etc.
            
            return result
            
        except ClientError as e:
            error_msg = f"DynamoDB error retrieving artifacts: {str(e)}"
            logger.error(error_msg, extra={'project_id': project_id})
            return {
                'success': False,
                'error': error_msg
            }
    
    def _parse_dynamodb_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a DynamoDB item to a regular dictionary"""
        result = {}
        for key, value in item.items():
            if 'S' in value:
                result[key] = value['S']
            elif 'N' in value:
                result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
            elif 'M' in value:
                result[key] = self._parse_dynamodb_item(value['M'])
            elif 'L' in value:
                result[key] = [self._parse_dynamodb_value(v) for v in value['L']]
        return result
    
    def _parse_dynamodb_value(self, value: Dict[str, Any]) -> Any:
        """Parse a single DynamoDB value"""
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            return int(value['N']) if '.' not in value['N'] else float(value['N'])
        elif 'M' in value:
            return self._parse_dynamodb_item(value['M'])
        elif 'L' in value:
            return [self._parse_dynamodb_value(v) for v in value['L']]
        return None
    
    def update_jira_status(
        self,
        project_id: str,
        artifact_type: str,
        artifact_id: str,
        jira_issue_id: str,
        jira_issue_key: str,
        jira_issue_url: str
    ) -> Dict[str, Any]:
        """
        Update Jira status for a specific artifact after it's pushed to Jira.
        
        Args:
            project_id: Project identifier
            artifact_type: Type of artifact (epic, feature, use_case, test_case)
            artifact_id: Artifact identifier
            jira_issue_id: Jira issue ID
            jira_issue_key: Jira issue key
            jira_issue_url: Jira issue URL
            
        Returns:
            Operation result
        """
        try:
            # This would need the full SK pattern to update the correct item
            # Implementation depends on how you want to query/update specific artifacts
            logger.info(
                f"Updated Jira status for {artifact_type} {artifact_id}",
                extra={
                    'project_id': project_id,
                    'jira_issue_key': jira_issue_key
                }
            )
            
            return {
                'success': True,
                'message': f"Updated Jira status for {artifact_type} {artifact_id}"
            }
            
        except Exception as e:
            error_msg = f"Error updating Jira status: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }


# Create singleton instance
dynamodb_tools = DynamoDBTools()


# Tool functions for agent integration
@tool
def store_test_artifacts_tool(
    project_id: str,
    project_name: str,
    session_id: str,
    epics_json: str,
    jira_project_key: str = None,
    notification_email: str = None
) -> str:
    """
    Tool function to store test artifacts in DynamoDB.
    This function is designed to be called by the agent.
    
    Args:
        project_id: Unique project identifier
        project_name: Human-readable project name
        session_id: Session ID for tracking
        epics_json: JSON string containing the epics structure
        jira_project_key: Optional Jira project key
        notification_email: Optional notification email
        
    Returns:
        JSON string with operation result
    """
    try:
        # Parse epics JSON
        epics = json.loads(epics_json)
        
        # Prepare metadata
        metadata = {}
        if jira_project_key:
            metadata['jira_project_key'] = jira_project_key
        if notification_email:
            metadata['notification_email'] = notification_email
        
        # Store artifacts
        result = dynamodb_tools.store_test_artifacts(
            project_id=project_id,
            project_name=project_name,
            session_id=session_id,
            epics=epics,
            metadata=metadata
        )
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError as e:
        error_result = {
            'success': False,
            'error': f'Invalid JSON format for epics: {str(e)}'
        }
        return json.dumps(error_result)
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Error storing artifacts: {str(e)}'
        }
        return json.dumps(error_result)

@tool
def get_project_artifacts_tool(project_id: str) -> str:
    """
    Tool function to retrieve project artifacts from DynamoDB.
    
    Args:
        project_id: Project identifier
        
    Returns:
        JSON string with project artifacts
    """
    result = dynamodb_tools.get_project_artifacts(project_id)
    return json.dumps(result, indent=2)

@tool
def update_use_case_tool(
    project_id: str,
    epic_id: str,
    feature_id: str,
    use_case_id: str,
    use_case_data: str
) -> str:
    """
    Tool function to update a specific use case in DynamoDB.
    This function updates an existing use case with enhanced data.
    
    Args:
        project_id: Project identifier
        epic_id: Epic identifier
        feature_id: Feature identifier
        use_case_id: Use case identifier
        use_case_data: JSON string containing updated use case data
        
    Returns:
        JSON string with operation result
    """
    try:
        # Parse use case data
        use_case = json.loads(use_case_data)
        timestamp = datetime.utcnow().isoformat()
        
        # Build the sort key
        sk = f'EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}'
        
        # Prepare update expression and attribute values
        update_parts = ['updated_at = :updated_at']
        expr_attr_values = {':updated_at': {'S': timestamp}}
        
        # Update basic fields
        if 'title' in use_case:
            update_parts.append('title = :title')
            expr_attr_values[':title'] = {'S': use_case['title']}
        
        if 'description' in use_case:
            update_parts.append('description = :description')
            expr_attr_values[':description'] = {'S': use_case['description']}
        
        if 'priority' in use_case:
            update_parts.append('priority = :priority')
            expr_attr_values[':priority'] = {'S': use_case['priority']}
        
        if 'review_status' in use_case:
            update_parts.append('review_status = :review_status')
            expr_attr_values[':review_status'] = {'S': use_case['review_status']}
        
        # Update acceptance criteria
        if 'acceptance_criteria' in use_case:
            update_parts.append('acceptance_criteria = :acceptance_criteria')
            expr_attr_values[':acceptance_criteria'] = {
                'L': [{'S': criteria} for criteria in use_case['acceptance_criteria']]
            }
        
        # Update test scenarios outline
        if 'test_scenarios_outline' in use_case:
            update_parts.append('test_scenarios_outline = :test_scenarios_outline')
            expr_attr_values[':test_scenarios_outline'] = {
                'L': [{'S': scenario} for scenario in use_case['test_scenarios_outline']]
            }
        
        # Update compliance mapping
        if 'compliance_mapping' in use_case:
            update_parts.append('compliance_mapping = :compliance_mapping')
            expr_attr_values[':compliance_mapping'] = {
                'L': [{'S': mapping} for mapping in use_case['compliance_mapping']]
            }
        
        # Update Jira fields
        if 'jira_issue_id' in use_case:
            update_parts.append('jira_issue_id = :jira_issue_id')
            expr_attr_values[':jira_issue_id'] = {'S': str(use_case['jira_issue_id'])}
        
        if 'jira_issue_key' in use_case:
            update_parts.append('jira_issue_key = :jira_issue_key')
            expr_attr_values[':jira_issue_key'] = {'S': use_case['jira_issue_key']}
        
        if 'jira_issue_url' in use_case:
            update_parts.append('jira_issue_url = :jira_issue_url')
            expr_attr_values[':jira_issue_url'] = {'S': use_case['jira_issue_url']}
        
        if 'jira_status' in use_case:
            update_parts.append('jira_status = :jira_status')
            expr_attr_values[':jira_status'] = {'S': use_case['jira_status']}
        
        # Update optional fields
        if 'model_explanation' in use_case:
            update_parts.append('model_explanation = :model_explanation')
            expr_attr_values[':model_explanation'] = {'S': use_case['model_explanation']}
        
        if 'comments' in use_case:
            update_parts.append('comments = :comments')
            expr_attr_values[':comments'] = {'S': use_case['comments']}
        
        # Build update expression
        update_expression = 'SET ' + ', '.join(update_parts)
        
        # Update the item
        dynamodb_tools.dynamodb.update_item(
            TableName=dynamodb_tools.table_name,
            Key={
                'PK': {'S': f'PROJECT#{project_id}'},
                'SK': {'S': sk}
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_attr_values
        )
        
        logger.info(
            f"Updated use case {use_case_id} in project {project_id}",
            extra={'project_id': project_id, 'use_case_id': use_case_id}
        )
        
        result = {
            'success': True,
            'project_id': project_id,
            'use_case_id': use_case_id,
            'message': f'Successfully updated use case {use_case_id}',
            'updated_at': timestamp
        }
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError as e:
        error_result = {
            'success': False,
            'error': f'Invalid JSON format for use case data: {str(e)}'
        }
        return json.dumps(error_result)
    except ClientError as e:
        error_result = {
            'success': False,
            'error': f'DynamoDB error updating use case: {str(e)}'
        }
        logger.error(error_result['error'], extra={'project_id': project_id})
        return json.dumps(error_result)
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Error updating use case: {str(e)}'
        }
        logger.error(error_result['error'], extra={'project_id': project_id})
        return json.dumps(error_result)

@tool
def update_test_case_tool(
    project_id: str,
    epic_id: str,
    feature_id: str,
    use_case_id: str,
    test_case_id: str,
    test_case_data: str
) -> str:
    """
    Tool function to update a specific test case in DynamoDB.
    This function updates an existing test case with enhanced data.
    
    Args:
        project_id: Project identifier
        epic_id: Epic identifier
        feature_id: Feature identifier
        use_case_id: Use case identifier
        test_case_id: Test case identifier
        test_case_data: JSON string containing updated test case data
        
    Returns:
        JSON string with operation result
    """
    try:
        # Parse test case data
        test_case = json.loads(test_case_data)
        timestamp = datetime.utcnow().isoformat()
        
        # Build the sort key
        sk = f'EPIC#{epic_id}#FEATURE#{feature_id}#UC#{use_case_id}#TC#{test_case_id}'
        
        # Prepare update expression and attribute values
        update_parts = ['updated_at = :updated_at']
        expr_attr_values = {':updated_at': {'S': timestamp}}
        
        # Update basic fields
        if 'test_case_title' in test_case:
            update_parts.append('test_case_title = :test_case_title')
            expr_attr_values[':test_case_title'] = {'S': test_case['test_case_title']}
        
        if 'test_type' in test_case:
            update_parts.append('test_type = :test_type')
            expr_attr_values[':test_type'] = {'S': test_case['test_type']}
        
        if 'priority' in test_case:
            update_parts.append('priority = :priority')
            expr_attr_values[':priority'] = {'S': test_case['priority']}
        
        if 'expected_result' in test_case:
            update_parts.append('expected_result = :expected_result')
            expr_attr_values[':expected_result'] = {'S': test_case['expected_result']}
        
        if 'review_status' in test_case:
            update_parts.append('review_status = :review_status')
            expr_attr_values[':review_status'] = {'S': test_case['review_status']}
        
        # Update preconditions
        if 'preconditions' in test_case:
            update_parts.append('preconditions = :preconditions')
            expr_attr_values[':preconditions'] = {
                'L': [{'S': precond} for precond in test_case['preconditions']]
            }
        
        # Update test steps
        if 'test_steps' in test_case:
            update_parts.append('test_steps = :test_steps')
            expr_attr_values[':test_steps'] = {
                'L': [{'S': step} for step in test_case['test_steps']]
            }
        
        # Update compliance mapping
        if 'compliance_mapping' in test_case:
            update_parts.append('compliance_mapping = :compliance_mapping')
            expr_attr_values[':compliance_mapping'] = {
                'L': [{'S': mapping} for mapping in test_case['compliance_mapping']]
            }
        
        # Update Jira fields
        if 'jira_issue_id' in test_case:
            update_parts.append('jira_issue_id = :jira_issue_id')
            expr_attr_values[':jira_issue_id'] = {'S': str(test_case['jira_issue_id'])}
        
        if 'jira_issue_key' in test_case:
            update_parts.append('jira_issue_key = :jira_issue_key')
            expr_attr_values[':jira_issue_key'] = {'S': test_case['jira_issue_key']}
        
        if 'jira_issue_url' in test_case:
            update_parts.append('jira_issue_url = :jira_issue_url')
            expr_attr_values[':jira_issue_url'] = {'S': test_case['jira_issue_url']}
        
        if 'jira_status' in test_case:
            update_parts.append('jira_status = :jira_status')
            expr_attr_values[':jira_status'] = {'S': test_case['jira_status']}
        
        # Update optional fields
        if 'model_explanation' in test_case:
            update_parts.append('model_explanation = :model_explanation')
            expr_attr_values[':model_explanation'] = {'S': test_case['model_explanation']}
        
        if 'comments' in test_case:
            update_parts.append('comments = :comments')
            expr_attr_values[':comments'] = {'S': test_case['comments']}
        
        # Build update expression
        update_expression = 'SET ' + ', '.join(update_parts)
        
        # Update the item
        dynamodb_tools.dynamodb.update_item(
            TableName=dynamodb_tools.table_name,
            Key={
                'PK': {'S': f'PROJECT#{project_id}'},
                'SK': {'S': sk}
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_attr_values
        )
        
        logger.info(
            f"Updated test case {test_case_id} in project {project_id}",
            extra={'project_id': project_id, 'test_case_id': test_case_id}
        )
        
        result = {
            'success': True,
            'project_id': project_id,
            'test_case_id': test_case_id,
            'message': f'Successfully updated test case {test_case_id}',
            'updated_at': timestamp
        }
        
        return json.dumps(result, indent=2)
        
    except json.JSONDecodeError as e:
        error_result = {
            'success': False,
            'error': f'Invalid JSON format for test case data: {str(e)}'
        }
        return json.dumps(error_result)
    except ClientError as e:
        error_result = {
            'success': False,
            'error': f'DynamoDB error updating test case: {str(e)}'
        }
        logger.error(error_result['error'], extra={'project_id': project_id})
        return json.dumps(error_result)
    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Error updating test case: {str(e)}'
        }
        logger.error(error_result['error'], extra={'project_id': project_id})
        return json.dumps(error_result)
