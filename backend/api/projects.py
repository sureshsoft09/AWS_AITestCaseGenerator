"""
Project Management API endpoints for MedAssureAI.
Handles project retrieval, artifact hierarchy, and export functionality.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.logger import logger
import io
import boto3
from botocore.exceptions import ClientError
from backend.config import config

router = APIRouter(prefix="/api/projects", tags=["projects"])


class Project(BaseModel):
    """Project model."""
    project_id: str
    project_name: str
    jira_project_key: Optional[str] = None
    created_at: str
    updated_at: str
    artifact_counts: dict


class ProjectListResponse(BaseModel):
    """Response model for project list."""
    projects: List[Project]
    total_count: int


class ProjectArtifactsResponse(BaseModel):
    """Response model for project artifacts from DynamoDB."""
    success: bool
    project_id: str
    project_name: Optional[str] = None
    metadata: Optional[dict] = None
    hierarchy: Optional[dict] = None
    error: Optional[str] = None


class Artifact(BaseModel):
    """Artifact model."""
    id: str
    type: str
    name: str
    description: str
    priority: str
    status: str
    jira_key: Optional[str] = None
    jira_url: Optional[str] = None
    compliance_mapping: List[str]
    children: Optional[List['Artifact']] = None


class ArtifactTreeResponse(BaseModel):
    """Response model for artifact hierarchy."""
    project_id: str
    project_name: str
    artifacts: List[Artifact]
    total_count: int


@router.get("/list", response_model=ProjectListResponse)
async def get_projects_list():
    """
    Get list of all projects from DynamoDB.
    Returns basic project information for dropdown selection.
    """
    try:
        logger.info("Fetching projects list from DynamoDB")
        
        # Initialize DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            region_name=config.AWS_REGION
        )
        
        table_name = config.DYNAMODB_TABLE_NAME
        
        # Scan table to find all METADATA items (each project has one METADATA record)
        response = dynamodb.scan(
            TableName=table_name,
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={
                ':sk': {'S': 'METADATA'}
            }
        )
        
        projects = []
        for item in response.get('Items', []):
            try:
                # Parse project metadata
                project = {
                    'project_id': item.get('project_id', {}).get('S', ''),
                    'project_name': item.get('project_name', {}).get('S', ''),
                    'jira_project_key': item.get('jira_project_key', {}).get('S', ''),
                    'created_at': item.get('created_at', {}).get('S', ''),
                    'updated_at': item.get('updated_at', {}).get('S', ''),
                    'artifact_counts': {}
                }
                
                # Parse artifact counts if present
                if 'artifact_counts' in item and 'M' in item['artifact_counts']:
                    counts_map = item['artifact_counts']['M']
                    project['artifact_counts'] = {
                        'epics': int(counts_map.get('epics', {}).get('N', '0')),
                        'features': int(counts_map.get('features', {}).get('N', '0')),
                        'use_cases': int(counts_map.get('use_cases', {}).get('N', '0')),
                        'test_cases': int(counts_map.get('test_cases', {}).get('N', '0'))
                    }
                
                projects.append(project)
                
            except Exception as e:
                logger.error(f"Error parsing project item: {str(e)}")
                continue
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = dynamodb.scan(
                TableName=table_name,
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={
                    ':sk': {'S': 'METADATA'}
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            for item in response.get('Items', []):
                try:
                    project = {
                        'project_id': item.get('project_id', {}).get('S', ''),
                        'project_name': item.get('project_name', {}).get('S', ''),
                        'jira_project_key': item.get('jira_project_key', {}).get('S', ''),
                        'created_at': item.get('created_at', {}).get('S', ''),
                        'updated_at': item.get('updated_at', {}).get('S', ''),
                        'artifact_counts': {}
                    }
                    
                    if 'artifact_counts' in item and 'M' in item['artifact_counts']:
                        counts_map = item['artifact_counts']['M']
                        project['artifact_counts'] = {
                            'epics': int(counts_map.get('epics', {}).get('N', '0')),
                            'features': int(counts_map.get('features', {}).get('N', '0')),
                            'use_cases': int(counts_map.get('use_cases', {}).get('N', '0')),
                            'test_cases': int(counts_map.get('test_cases', {}).get('N', '0'))
                        }
                    
                    projects.append(project)
                    
                except Exception as e:
                    logger.error(f"Error parsing project item: {str(e)}")
                    continue
        
        logger.info(f"Found {len(projects)} projects")
        
        return {
            "projects": projects,
            "total_count": len(projects)
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error fetching projects list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects list: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching projects list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects list: {str(e)}"
        )


@router.get("/{project_id}/artifacts", response_model=ProjectArtifactsResponse)
async def get_project_artifacts(project_id: str):
    """
    Get complete artifact hierarchy for a project from DynamoDB.
    
    Args:
        project_id: Project identifier
        
    Returns:
        Complete project hierarchy with epics, features, use cases, and test cases
    """
    try:
        logger.info(f"Fetching artifacts for project: {project_id}")
        
        # Initialize DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            region_name=config.AWS_REGION
        )
        
        table_name = config.DYNAMODB_TABLE_NAME
        
        # Query all items for this project
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': {'S': f'PROJECT#{project_id}'}
            }
        )
        
        items = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = dynamodb.query(
                TableName=table_name,
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': {'S': f'PROJECT#{project_id}'}
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        if not items:
            logger.warning(f"No artifacts found for project {project_id}")
            return {
                "success": False,
                "project_id": project_id,
                "error": f"No artifacts found for project {project_id}"
            }
        
        # Parse items and organize by type
        metadata = None
        epics_map = {}
        features_map = {}
        use_cases_map = {}
        test_cases_map = {}
        
        for item in items:
            sk = item['SK']['S']
            
            if sk == 'METADATA':
                # Parse metadata
                metadata = _parse_dynamodb_item(item)
                
            elif sk.startswith('EPIC#') and '#FEATURE#' not in sk:
                # Epic item
                epic = _parse_dynamodb_item(item)
                epic['features'] = []
                epics_map[epic.get('epic_id', '')] = epic
                
            elif '#FEATURE#' in sk and '#UC#' not in sk:
                # Feature item
                feature = _parse_dynamodb_item(item)
                feature['use_cases'] = []
                epic_id = feature.get('epic_id', '')
                features_map[feature.get('feature_id', '')] = {
                    'data': feature,
                    'epic_id': epic_id
                }
                
            elif '#UC#' in sk and '#TC#' not in sk:
                # Use case item
                use_case = _parse_dynamodb_item(item)
                use_case['test_cases'] = []
                feature_id = use_case.get('feature_id', '')
                use_cases_map[use_case.get('use_case_id', '')] = {
                    'data': use_case,
                    'feature_id': feature_id
                }
                
            elif '#TC#' in sk:
                # Test case item
                test_case = _parse_dynamodb_item(item)
                use_case_id = test_case.get('use_case_id', '')
                if use_case_id not in test_cases_map:
                    test_cases_map[use_case_id] = []
                test_cases_map[use_case_id].append(test_case)
        
        # Reconstruct hierarchy: test cases → use cases → features → epics
        for use_case_id, test_cases_list in test_cases_map.items():
            if use_case_id in use_cases_map:
                use_cases_map[use_case_id]['data']['test_cases'] = test_cases_list
        
        for use_case_id, use_case_info in use_cases_map.items():
            feature_id = use_case_info['feature_id']
            if feature_id in features_map:
                features_map[feature_id]['data']['use_cases'].append(use_case_info['data'])
        
        for feature_id, feature_info in features_map.items():
            epic_id = feature_info['epic_id']
            if epic_id in epics_map:
                epics_map[epic_id]['features'].append(feature_info['data'])
        
        # Convert epics_map to list
        epics_list = list(epics_map.values())
        
        # Build response
        response_data = {
            "success": True,
            "project_id": project_id,
            "project_name": metadata.get('project_name', '') if metadata else '',
            "metadata": metadata,
            "hierarchy": {
                "epics": epics_list
            }
        }
        
        logger.info(f"Successfully retrieved {len(epics_list)} epics for project {project_id}")
        
        return response_data
        
    except ClientError as e:
        error_msg = f"DynamoDB error fetching project artifacts: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "project_id": project_id,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error fetching project artifacts: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "project_id": project_id,
            "error": error_msg
        }


def _parse_dynamodb_item(item: dict) -> dict:
    """
    Parse a DynamoDB item to a regular dictionary.
    Handles all DynamoDB data types (S, N, M, L, etc.)
    """
    result = {}
    for key, value in item.items():
        if 'S' in value:
            result[key] = value['S']
        elif 'N' in value:
            result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
        elif 'M' in value:
            result[key] = _parse_dynamodb_item(value['M'])
        elif 'L' in value:
            result[key] = [_parse_dynamodb_value(v) for v in value['L']]
        elif 'BOOL' in value:
            result[key] = value['BOOL']
        elif 'NULL' in value:
            result[key] = None
    return result


def _parse_dynamodb_value(value: dict) -> any:
    """Parse a single DynamoDB value"""
    if 'S' in value:
        return value['S']
    elif 'N' in value:
        return int(value['N']) if '.' not in value['N'] else float(value['N'])
    elif 'M' in value:
        return _parse_dynamodb_item(value['M'])
    elif 'L' in value:
        return [_parse_dynamodb_value(v) for v in value['L']]
    elif 'BOOL' in value:
        return value['BOOL']
    elif 'NULL' in value:
        return None
    return None


@router.get("", response_model=ProjectListResponse)
async def get_projects():
    """
    Retrieve all projects from DynamoDB.
    
    This endpoint:
    1. Queries DynamoDB for all projects
    2. Retrieves artifact counts for each project
    3. Returns list of projects with metadata
    
    Returns:
        List of projects with counts
    """
    try:
        logger.info("Retrieving all projects")
        
        # Simulate DynamoDB query
        # In production, this would query DynamoDB via MCP Server or boto3
        projects = _get_all_projects()
        
        logger.info(
            "Projects retrieved",
            extra={"project_count": len(projects)}
        )
        
        return {
            "projects": projects,
            "total_count": len(projects)
        }
        
    except Exception as e:
        logger.error(
            "Failed to retrieve projects",
            extra={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve projects: {str(e)}"
        )


@router.get("/{project_id}/artifacts", response_model=ArtifactTreeResponse)
async def get_project_artifacts(project_id: str):
    """
    Retrieve and reconstruct hierarchical artifact tree for a project.
    
    This endpoint:
    1. Queries DynamoDB for all artifacts in project
    2. Reconstructs hierarchical relationships (epic → feature → use case → test case)
    3. Returns nested artifact tree
    
    Args:
        project_id: Project identifier
        
    Returns:
        Hierarchical artifact tree
    """
    try:
        logger.info(
            "Retrieving project artifacts",
            extra={"project_id": project_id}
        )
        
        # Get project info
        project = _get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Get all artifacts for project
        all_artifacts = _get_project_artifacts(project_id)
        
        # Reconstruct hierarchy
        artifact_tree = _reconstruct_hierarchy(all_artifacts)
        
        logger.info(
            "Project artifacts retrieved",
            extra={
                "project_id": project_id,
                "total_artifacts": len(all_artifacts)
            }
        )
        
        return {
            "project_id": project_id,
            "project_name": project.get("project_name", "Unknown"),
            "artifacts": artifact_tree,
            "total_count": len(all_artifacts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve project artifacts",
            extra={"project_id": project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project artifacts: {str(e)}"
        )


@router.get("/{project_id}/export")
async def export_project(
    project_id: str,
    format: str = Query(..., regex="^(excel|xml)$", description="Export format: excel or xml")
):
    """
    Generate and return export file for project artifacts.
    
    This endpoint:
    1. Retrieves all artifacts for project
    2. Generates export file in requested format (Excel or XML)
    3. Returns file as downloadable response
    
    Args:
        project_id: Project identifier
        format: Export format (excel or xml)
        
    Returns:
        File download response
    """
    try:
        logger.info(
            "Exporting project",
            extra={"project_id": project_id, "format": format}
        )
        
        # Get project info
        project = _get_project_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Get all artifacts
        all_artifacts = _get_project_artifacts(project_id)
        
        if format == "excel":
            # Generate Excel file
            file_content, filename = _generate_excel_export(project, all_artifacts)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:  # xml
            # Generate XML file
            file_content, filename = _generate_xml_export(project, all_artifacts)
            media_type = "application/xml"
        
        logger.info(
            "Project exported",
            extra={
                "project_id": project_id,
                "format": format,
                "artifact_count": len(all_artifacts)
            }
        )
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to export project",
            extra={"project_id": project_id, "format": format, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project: {str(e)}"
        )


def _get_all_projects() -> List[dict]:
    """
    Get all projects from DynamoDB.
    
    In production, this would query DynamoDB via MCP Server or boto3.
    """
    # Simulate projects
    return [
        {
            "project_id": "proj-001",
            "project_name": "Healthcare Portal",
            "jira_project_key": "HCP",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-20T15:30:00Z",
            "artifact_counts": {
                "epics": 3,
                "features": 8,
                "use_cases": 15,
                "test_cases": 45,
                "total": 71
            }
        },
        {
            "project_id": "proj-002",
            "project_name": "Patient Management System",
            "jira_project_key": "PMS",
            "created_at": "2024-01-10T09:00:00Z",
            "updated_at": "2024-01-18T14:20:00Z",
            "artifact_counts": {
                "epics": 5,
                "features": 12,
                "use_cases": 25,
                "test_cases": 80,
                "total": 122
            }
        },
        {
            "project_id": "proj-003",
            "project_name": "Medical Records System",
            "jira_project_key": "MRS",
            "created_at": "2024-01-05T08:00:00Z",
            "updated_at": "2024-01-22T16:45:00Z",
            "artifact_counts": {
                "epics": 4,
                "features": 10,
                "use_cases": 20,
                "test_cases": 65,
                "total": 99
            }
        }
    ]


def _get_project_by_id(project_id: str) -> Optional[dict]:
    """
    Get project by ID from DynamoDB.
    
    In production, this would query DynamoDB via MCP Server or boto3.
    """
    projects = _get_all_projects()
    for project in projects:
        if project["project_id"] == project_id:
            return project
    return None


def _get_project_artifacts(project_id: str) -> List[dict]:
    """
    Get all artifacts for a project from DynamoDB.
    
    In production, this would query DynamoDB via MCP Server or boto3.
    """
    # Simulate artifacts with hierarchical relationships
    return [
        # Epics
        {
            "id": "E001",
            "type": "epic",
            "name": "User Authentication",
            "description": "Implement secure user authentication system",
            "priority": "Critical",
            "status": "Active",
            "jira_key": "HCP-E001",
            "jira_url": "https://jira.example.com/browse/HCP-E001",
            "compliance_mapping": ["HIPAA", "ISO_27001"],
            "parent_id": None
        },
        # Features
        {
            "id": "F001",
            "type": "feature",
            "name": "Login Functionality",
            "description": "User login with credentials",
            "priority": "High",
            "status": "Active",
            "jira_key": "HCP-F001",
            "jira_url": "https://jira.example.com/browse/HCP-F001",
            "compliance_mapping": ["HIPAA", "ISO_27001"],
            "parent_id": "E001"
        },
        {
            "id": "F002",
            "type": "feature",
            "name": "Password Reset",
            "description": "Allow users to reset forgotten passwords",
            "priority": "Medium",
            "status": "Active",
            "jira_key": "HCP-F002",
            "jira_url": "https://jira.example.com/browse/HCP-F002",
            "compliance_mapping": ["HIPAA"],
            "parent_id": "E001"
        },
        # Use Cases
        {
            "id": "UC001",
            "type": "use_case",
            "name": "Valid User Login",
            "description": "User logs in with valid credentials",
            "priority": "High",
            "status": "Active",
            "jira_key": "HCP-UC001",
            "jira_url": "https://jira.example.com/browse/HCP-UC001",
            "compliance_mapping": ["HIPAA", "ISO_27001"],
            "parent_id": "F001"
        },
        {
            "id": "UC002",
            "type": "use_case",
            "name": "Invalid User Login",
            "description": "User attempts login with invalid credentials",
            "priority": "High",
            "status": "Active",
            "jira_key": "HCP-UC002",
            "jira_url": "https://jira.example.com/browse/HCP-UC002",
            "compliance_mapping": ["HIPAA", "ISO_27001"],
            "parent_id": "F001"
        },
        # Test Cases
        {
            "id": "TC001",
            "type": "test_case",
            "name": "Test Valid Login",
            "description": "Verify user can login with valid credentials",
            "priority": "High",
            "status": "Active",
            "jira_key": "HCP-TC001",
            "jira_url": "https://jira.example.com/browse/HCP-TC001",
            "compliance_mapping": ["HIPAA", "ISO_27001"],
            "parent_id": "UC001"
        },
        {
            "id": "TC002",
            "type": "test_case",
            "name": "Test Invalid Username",
            "description": "Verify error message for invalid username",
            "priority": "Medium",
            "status": "Active",
            "jira_key": "HCP-TC002",
            "jira_url": "https://jira.example.com/browse/HCP-TC002",
            "compliance_mapping": ["HIPAA"],
            "parent_id": "UC002"
        },
        {
            "id": "TC003",
            "type": "test_case",
            "name": "Test Invalid Password",
            "description": "Verify error message for invalid password",
            "priority": "Medium",
            "status": "Active",
            "jira_key": "HCP-TC003",
            "jira_url": "https://jira.example.com/browse/HCP-TC003",
            "compliance_mapping": ["HIPAA"],
            "parent_id": "UC002"
        }
    ]


def _reconstruct_hierarchy(artifacts: List[dict]) -> List[dict]:
    """
    Reconstruct hierarchical artifact tree from flat list.
    
    Builds parent-child relationships: epic → feature → use case → test case
    """
    # Create lookup dictionary
    artifact_map = {artifact["id"]: artifact.copy() for artifact in artifacts}
    
    # Initialize children lists
    for artifact in artifact_map.values():
        artifact["children"] = []
    
    # Build hierarchy
    root_artifacts = []
    
    for artifact in artifact_map.values():
        parent_id = artifact.get("parent_id")
        
        if parent_id and parent_id in artifact_map:
            # Add to parent's children
            artifact_map[parent_id]["children"].append(artifact)
        else:
            # Root level artifact (no parent)
            root_artifacts.append(artifact)
    
    # Remove parent_id from output (not needed in response)
    def clean_artifact(artifact):
        artifact.pop("parent_id", None)
        if not artifact["children"]:
            artifact.pop("children", None)
        else:
            for child in artifact["children"]:
                clean_artifact(child)
        return artifact
    
    return [clean_artifact(artifact) for artifact in root_artifacts]


def _generate_excel_export(project: dict, artifacts: List[dict]) -> tuple:
    """
    Generate Excel export file.
    
    In production, this would use openpyxl or xlsxwriter.
    Returns (file_content, filename) tuple.
    """
    # Simulate Excel generation
    # In production, create actual Excel file with multiple sheets
    
    project_name = project.get("project_name", "project").replace(" ", "_")
    filename = f"{project_name}_artifacts.xlsx"
    
    # Simulate Excel content (would be actual Excel binary)
    content = b"Excel file content placeholder"
    
    return content, filename


def _generate_xml_export(project: dict, artifacts: List[dict]) -> tuple:
    """
    Generate XML export file.
    
    In production, this would use xml.etree.ElementTree or lxml.
    Returns (file_content, filename) tuple.
    """
    # Simulate XML generation
    project_name = project.get("project_name", "project").replace(" ", "_")
    filename = f"{project_name}_artifacts.xml"
    
    # Build XML structure
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project>
    <project_id>{project.get('project_id')}</project_id>
    <project_name>{project.get('project_name')}</project_name>
    <jira_project_key>{project.get('jira_project_key')}</jira_project_key>
    <artifacts>
"""
    
    for artifact in artifacts:
        xml_content += f"""        <artifact>
            <id>{artifact.get('id')}</id>
            <type>{artifact.get('type')}</type>
            <name>{artifact.get('name')}</name>
            <description>{artifact.get('description')}</description>
            <priority>{artifact.get('priority')}</priority>
            <status>{artifact.get('status')}</status>
            <jira_key>{artifact.get('jira_key')}</jira_key>
            <compliance_mapping>{','.join(artifact.get('compliance_mapping', []))}</compliance_mapping>
        </artifact>
"""
    
    xml_content += """    </artifacts>
</project>"""
    
    return xml_content.encode('utf-8'), filename
