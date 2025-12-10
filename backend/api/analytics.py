"""
Analytics API endpoints for MedAssureAI.
Handles project analytics, priority distribution, and compliance coverage.
"""
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.logger import logger

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class PriorityDistribution(BaseModel):
    """Priority distribution model."""
    priority: str
    count: int
    percentage: float


class PriorityAnalyticsResponse(BaseModel):
    """Response model for priority analytics."""
    project_id: str
    total_artifacts: int
    distribution: List[PriorityDistribution]


class ComplianceStandard(BaseModel):
    """Compliance standard coverage model."""
    standard: str
    covered_artifacts: int
    total_artifacts: int
    coverage_percentage: float


class ComplianceAnalyticsResponse(BaseModel):
    """Response model for compliance analytics."""
    project_id: str
    total_artifacts: int
    standards: List[ComplianceStandard]


class ProjectSummary(BaseModel):
    """Project summary statistics model."""
    project_id: str
    project_name: str
    total_artifacts: int
    artifact_breakdown: Dict[str, int]
    priority_summary: Dict[str, int]
    compliance_summary: Dict[str, float]
    status_summary: Dict[str, int]


@router.get("/{project_id}/priority", response_model=PriorityAnalyticsResponse)
async def get_priority_analytics(project_id: str):
    """
    Get artifact count distribution by priority.
    
    This endpoint:
    1. Queries DynamoDB for all artifacts in project
    2. Aggregates counts by priority level
    3. Calculates percentages
    4. Returns priority distribution
    
    Args:
        project_id: Project identifier
        
    Returns:
        Priority distribution with counts and percentages
    """
    try:
        logger.info(
            "Retrieving priority analytics",
            extra={"project_id": project_id}
        )
        
        # Get all artifacts for project
        artifacts = _get_project_artifacts(project_id)
        
        if not artifacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found or has no artifacts"
            )
        
        # Aggregate by priority
        priority_counts = {}
        for artifact in artifacts:
            priority = artifact.get("priority", "Unknown")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        total_artifacts = len(artifacts)
        
        # Calculate percentages and build distribution
        distribution = []
        for priority in ["Critical", "High", "Medium", "Low"]:
            count = priority_counts.get(priority, 0)
            percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
            distribution.append({
                "priority": priority,
                "count": count,
                "percentage": round(percentage, 2)
            })
        
        # Add any other priorities not in standard list
        for priority, count in priority_counts.items():
            if priority not in ["Critical", "High", "Medium", "Low"]:
                percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
                distribution.append({
                    "priority": priority,
                    "count": count,
                    "percentage": round(percentage, 2)
                })
        
        logger.info(
            "Priority analytics retrieved",
            extra={
                "project_id": project_id,
                "total_artifacts": total_artifacts
            }
        )
        
        return {
            "project_id": project_id,
            "total_artifacts": total_artifacts,
            "distribution": distribution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve priority analytics",
            extra={"project_id": project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve priority analytics: {str(e)}"
        )


@router.get("/{project_id}/compliance", response_model=ComplianceAnalyticsResponse)
async def get_compliance_analytics(project_id: str):
    """
    Get compliance coverage percentages by standard.
    
    This endpoint:
    1. Queries DynamoDB for all artifacts in project
    2. Analyzes compliance_mapping tags
    3. Calculates coverage percentage for each standard
    4. Returns compliance coverage matrix
    
    Args:
        project_id: Project identifier
        
    Returns:
        Compliance coverage by standard
    """
    try:
        logger.info(
            "Retrieving compliance analytics",
            extra={"project_id": project_id}
        )
        
        # Get all artifacts for project
        artifacts = _get_project_artifacts(project_id)
        
        if not artifacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found or has no artifacts"
            )
        
        total_artifacts = len(artifacts)
        
        # Aggregate compliance coverage
        compliance_counts = {}
        
        for artifact in artifacts:
            compliance_mapping = artifact.get("compliance_mapping", [])
            for standard in compliance_mapping:
                compliance_counts[standard] = compliance_counts.get(standard, 0) + 1
        
        # Build standards list with coverage percentages
        standards = []
        
        # Common standards to check
        common_standards = [
            "FDA_21_CFR_Part_11",
            "IEC_62304",
            "ISO_9001",
            "ISO_13485",
            "ISO_27001",
            "HIPAA",
            "GDPR"
        ]
        
        for standard in common_standards:
            covered_count = compliance_counts.get(standard, 0)
            coverage_percentage = (covered_count / total_artifacts * 100) if total_artifacts > 0 else 0
            
            if covered_count > 0:  # Only include standards that have coverage
                standards.append({
                    "standard": standard,
                    "covered_artifacts": covered_count,
                    "total_artifacts": total_artifacts,
                    "coverage_percentage": round(coverage_percentage, 2)
                })
        
        # Add any other standards not in common list
        for standard, count in compliance_counts.items():
            if standard not in common_standards:
                coverage_percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
                standards.append({
                    "standard": standard,
                    "covered_artifacts": count,
                    "total_artifacts": total_artifacts,
                    "coverage_percentage": round(coverage_percentage, 2)
                })
        
        # Sort by coverage percentage descending
        standards.sort(key=lambda x: x["coverage_percentage"], reverse=True)
        
        logger.info(
            "Compliance analytics retrieved",
            extra={
                "project_id": project_id,
                "standards_count": len(standards)
            }
        )
        
        return {
            "project_id": project_id,
            "total_artifacts": total_artifacts,
            "standards": standards
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve compliance analytics",
            extra={"project_id": project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve compliance analytics: {str(e)}"
        )


@router.get("/{project_id}/summary", response_model=ProjectSummary)
async def get_project_summary(project_id: str):
    """
    Get overall project statistics and summary.
    
    This endpoint:
    1. Queries DynamoDB for all artifacts in project
    2. Aggregates counts by type, priority, status
    3. Calculates compliance coverage summary
    4. Returns comprehensive project statistics
    
    Args:
        project_id: Project identifier
        
    Returns:
        Comprehensive project summary
    """
    try:
        logger.info(
            "Retrieving project summary",
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
        artifacts = _get_project_artifacts(project_id)
        
        total_artifacts = len(artifacts)
        
        # Aggregate by type
        artifact_breakdown = {}
        for artifact in artifacts:
            artifact_type = artifact.get("type", "unknown")
            artifact_breakdown[artifact_type] = artifact_breakdown.get(artifact_type, 0) + 1
        
        # Aggregate by priority
        priority_summary = {}
        for artifact in artifacts:
            priority = artifact.get("priority", "Unknown")
            priority_summary[priority] = priority_summary.get(priority, 0) + 1
        
        # Aggregate by status
        status_summary = {}
        for artifact in artifacts:
            artifact_status = artifact.get("status", "Unknown")
            status_summary[artifact_status] = status_summary.get(artifact_status, 0) + 1
        
        # Calculate compliance coverage summary
        compliance_counts = {}
        for artifact in artifacts:
            compliance_mapping = artifact.get("compliance_mapping", [])
            for standard in compliance_mapping:
                compliance_counts[standard] = compliance_counts.get(standard, 0) + 1
        
        compliance_summary = {}
        for standard, count in compliance_counts.items():
            coverage_percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
            compliance_summary[standard] = round(coverage_percentage, 2)
        
        logger.info(
            "Project summary retrieved",
            extra={
                "project_id": project_id,
                "total_artifacts": total_artifacts
            }
        )
        
        return {
            "project_id": project_id,
            "project_name": project.get("project_name", "Unknown"),
            "total_artifacts": total_artifacts,
            "artifact_breakdown": artifact_breakdown,
            "priority_summary": priority_summary,
            "compliance_summary": compliance_summary,
            "status_summary": status_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve project summary",
            extra={"project_id": project_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve project summary: {str(e)}"
        )


def _get_project_by_id(project_id: str) -> dict:
    """
    Get project by ID from DynamoDB.
    
    In production, this would query DynamoDB via MCP Server or boto3.
    """
    # Simulate project lookup
    projects = {
        "proj-001": {
            "project_id": "proj-001",
            "project_name": "Healthcare Portal",
            "jira_project_key": "HCP"
        },
        "proj-002": {
            "project_id": "proj-002",
            "project_name": "Patient Management System",
            "jira_project_key": "PMS"
        },
        "proj-003": {
            "project_id": "proj-003",
            "project_name": "Medical Records System",
            "jira_project_key": "MRS"
        }
    }
    
    return projects.get(project_id)


def _get_project_artifacts(project_id: str) -> List[dict]:
    """
    Get all artifacts for a project from DynamoDB.
    
    In production, this would query DynamoDB via MCP Server or boto3.
    """
    # Simulate artifacts with various priorities, statuses, and compliance mappings
    return [
        {
            "id": "E001",
            "type": "epic",
            "priority": "Critical",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001", "GDPR"]
        },
        {
            "id": "E002",
            "type": "epic",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "IEC_62304"]
        },
        {
            "id": "E003",
            "type": "epic",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["ISO_9001", "ISO_13485"]
        },
        {
            "id": "F001",
            "type": "feature",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001"]
        },
        {
            "id": "F002",
            "type": "feature",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "GDPR"]
        },
        {
            "id": "F003",
            "type": "feature",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["ISO_9001"]
        },
        {
            "id": "F004",
            "type": "feature",
            "priority": "Medium",
            "status": "Draft",
            "compliance_mapping": ["ISO_13485"]
        },
        {
            "id": "F005",
            "type": "feature",
            "priority": "Low",
            "status": "Active",
            "compliance_mapping": ["ISO_9001"]
        },
        {
            "id": "UC001",
            "type": "use_case",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001"]
        },
        {
            "id": "UC002",
            "type": "use_case",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001"]
        },
        {
            "id": "UC003",
            "type": "use_case",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["HIPAA"]
        },
        {
            "id": "UC004",
            "type": "use_case",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["ISO_9001"]
        },
        {
            "id": "UC005",
            "type": "use_case",
            "priority": "Low",
            "status": "Draft",
            "compliance_mapping": ["ISO_9001"]
        },
        {
            "id": "TC001",
            "type": "test_case",
            "priority": "Critical",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001", "GDPR"]
        },
        {
            "id": "TC002",
            "type": "test_case",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA", "ISO_27001"]
        },
        {
            "id": "TC003",
            "type": "test_case",
            "priority": "High",
            "status": "Active",
            "compliance_mapping": ["HIPAA"]
        },
        {
            "id": "TC004",
            "type": "test_case",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["ISO_9001", "ISO_13485"]
        },
        {
            "id": "TC005",
            "type": "test_case",
            "priority": "Medium",
            "status": "Active",
            "compliance_mapping": ["ISO_9001"]
        },
        {
            "id": "TC006",
            "type": "test_case",
            "priority": "Low",
            "status": "Draft",
            "compliance_mapping": ["ISO_9001"]
        }
    ]
