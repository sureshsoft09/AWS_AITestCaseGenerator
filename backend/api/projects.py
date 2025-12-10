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
