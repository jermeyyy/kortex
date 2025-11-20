import logging
import sys
from pathlib import Path
import pytest
from kortex_mcp.utils.logging import setup_logging, get_logger

class TestLogging:
    def test_get_logger(self):
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logging_defaults(self, capsys):
        setup_logging(level=logging.INFO)
        logger = get_logger("test_defaults")
        logger.info("Info message")
        logger.debug("Debug message")
        
        captured = capsys.readouterr()
        assert "Info message" in captured.out
        assert "Debug message" not in captured.out

    def test_setup_logging_custom_level(self, capsys):
        setup_logging(level=logging.DEBUG)
        logger = get_logger("test_debug")
        logger.debug("Debug message")
        
        captured = capsys.readouterr()
        assert "Debug message" in captured.out

    def test_setup_logging_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging(level=logging.INFO, log_file=log_file)
        
        logger = get_logger("test_file")
        logger.info("File message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "File message" in content

    def test_setup_logging_custom_format(self, capsys):
        custom_format = "CUSTOM: %(message)s"
        setup_logging(level=logging.INFO, format_string=custom_format)
        
        logger = get_logger("test_format")
        logger.info("Formatted message")
        
        captured = capsys.readouterr()
        assert "CUSTOM: Formatted message" in captured.out
