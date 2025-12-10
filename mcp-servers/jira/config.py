"""
Configuration management for Jira MCP Server.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Jira MCP Server."""
    
    # Jira Configuration
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    
    # AWS Configuration (for logging/monitoring)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BACKOFF_FACTOR: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))


config = Config()
