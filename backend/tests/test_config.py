"""
Tests for configuration management.
Validates that configuration loads correctly.
"""
import pytest
from backend.config import Config


def test_config_has_required_attributes():
    """Test that Config class has all required attributes."""
    config = Config()
    
    # AWS Configuration
    assert hasattr(config, 'AWS_REGION')
    assert hasattr(config, 'AWS_ACCESS_KEY_ID')
    assert hasattr(config, 'AWS_SECRET_ACCESS_KEY')
    
    # S3 Configuration
    assert hasattr(config, 'S3_INGEST_BUCKET')
    assert hasattr(config, 'S3_FRONTEND_BUCKET')
    
    # DynamoDB Configuration
    assert hasattr(config, 'DYNAMODB_TABLE_NAME')
    
    # Application Configuration
    assert hasattr(config, 'LOG_LEVEL')
    assert hasattr(config, 'ENVIRONMENT')


def test_config_default_values():
    """Test that Config has sensible default values."""
    config = Config()
    
    assert config.AWS_REGION == "us-east-1"
    assert config.DYNAMODB_TABLE_NAME == "MedAssureAI_Artifacts"
    assert config.LOG_LEVEL == "INFO"
    assert config.ENVIRONMENT == "development"


def test_config_validation_with_defaults():
    """Test that config validation works with default values."""
    config = Config()
    
    # Should not raise with default values
    assert config.validate() is True
