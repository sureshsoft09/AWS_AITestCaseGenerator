"""
Configuration for MedAssureAI Agents Service
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in agents directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class AgentConfig:
    """Configuration for agents service"""
    
    # AWS Bedrock Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
    
    # OpenSearch Configuration
    OPENSEARCH_ENDPOINT = os.getenv('OPENSEARCH_ENDPOINT', '')
    OPENSEARCH_INDEX = os.getenv('OPENSEARCH_INDEX', 'medassure_sessions')
    
    # Service Configuration
    SERVICE_NAME = 'medassure-agents'
    SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8001'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


# Create singleton instance
agent_config = AgentConfig()

# Set OpenSearch host for mem0_memory tool
if agent_config.OPENSEARCH_ENDPOINT:
    # Extract hostname from endpoint URL (remove https://)
    opensearch_host = agent_config.OPENSEARCH_ENDPOINT.replace('https://', '').replace('http://', '')
    os.environ["OPENSEARCH_HOST"] = opensearch_host
    os.environ["AWS_REGION"] = agent_config.AWS_REGION
    
    # Configure mem0 to use the correct Bedrock model for embeddings
    # mem0 uses titan-embed-text-v1 by default, which is available in Bedrock
    os.environ["EMBEDDER_MODEL"] = "amazon.titan-embed-text-v1"
    os.environ["LLM_MODEL"] = agent_config.BEDROCK_MODEL_ID
