"""
Tests for logging configuration.
Validates that logger is properly configured.
"""
import logging
import pytest
from backend.logger import setup_logger, CustomJsonFormatter


def test_setup_logger_returns_logger():
    """Test that setup_logger returns a Logger instance."""
    logger = setup_logger("test_logger")
    assert isinstance(logger, logging.Logger)


def test_logger_has_handler():
    """Test that logger has at least one handler."""
    logger = setup_logger("test_logger_handler")
    assert len(logger.handlers) > 0


def test_logger_handler_has_json_formatter():
    """Test that logger handler uses CustomJsonFormatter."""
    logger = setup_logger("test_logger_formatter")
    handler = logger.handlers[0]
    assert isinstance(handler.formatter, CustomJsonFormatter)


def test_logger_level_from_config():
    """Test that logger level is set from config."""
    logger = setup_logger("test_logger_level")
    # Default log level should be INFO
    assert logger.level == logging.INFO


def test_logger_does_not_propagate():
    """Test that logger does not propagate to root logger."""
    logger = setup_logger("test_logger_propagate")
    assert logger.propagate is False
