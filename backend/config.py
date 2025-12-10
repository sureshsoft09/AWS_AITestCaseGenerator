"""
Configuration management for MedAssureAI backend.
Loads settings from environment variables with fallback to .env file.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration class."""
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_SESSION_TOKEN: Optional[str] = os.getenv("AWS_SESSION_TOKEN")  # For temporary credentials
    
    # S3 Configuration
    S3_INGEST_BUCKET: str = os.getenv("S3_INGEST_BUCKET", "medassure-ingest-bucket")
    S3_FRONTEND_BUCKET: str = os.getenv("S3_FRONTEND_BUCKET", "medassure-frontend-bucket")
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "MedAssureAI_Artifacts")
    
    # OpenSearch Configuration
    OPENSEARCH_ENDPOINT: str = os.getenv("OPENSEARCH_ENDPOINT", "")
    OPENSEARCH_USERNAME: str = os.getenv("OPENSEARCH_USERNAME", "admin")
    OPENSEARCH_PASSWORD: str = os.getenv("OPENSEARCH_PASSWORD", "")
    
    # Jira Configuration
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-v2")
    BEDROCK_REGION: str = os.getenv("BEDROCK_REGION", "us-east-1")
    
    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Email Notification (SES)
    NOTIFICATION_FROM_EMAIL: str = os.getenv("NOTIFICATION_FROM_EMAIL", "noreply@medassure.com")
    SES_SENDER_EMAIL: str = os.getenv("SES_SENDER_EMAIL", "noreply@medassure.com")
    SES_REGION: str = os.getenv("SES_REGION", "us-east-1")
    
    # MCP Server Endpoints
    JIRA_MCP_SERVER_URL: str = os.getenv("JIRA_MCP_SERVER_URL", "http://localhost:8001")
    DYNAMODB_MCP_SERVER_URL: str = os.getenv("DYNAMODB_MCP_SERVER_URL", "http://localhost:8002")
    
    # Authentication Configuration (Cognito)
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_APP_CLIENT_ID: str = os.getenv("COGNITO_APP_CLIENT_ID", "")
    COGNITO_REGION: str = os.getenv("COGNITO_REGION", "us-east-1")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values are present."""
        required_fields = [
            "AWS_REGION",
            "S3_INGEST_BUCKET",
            "DYNAMODB_TABLE_NAME",
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True


# Create a singleton instance
config = Config()
