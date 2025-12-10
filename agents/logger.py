"""
Logging configuration for MedAssureAI Agents Service
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from agents.config import agent_config


def setup_logger(name: str = 'medassure_agents') -> logging.Logger:
    """
    Set up JSON logger for agents service.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, agent_config.LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, agent_config.LOG_LEVEL))
    
    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={'asctime': 'timestamp', 'levelname': 'level'}
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Create default logger
logger = setup_logger()
