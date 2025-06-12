#!/usr/bin/env python3
"""
Logger configuration for the application.
"""
import logging
from pathlib import Path
import os
import sys
from datetime import datetime

def setup_logging(level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        level: The logging level to use
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Configure formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure file handler
    try:
        logs_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Use timestamp to create unique log file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = logs_dir / f"transcript_editor_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Add a reference to the log file
        root_logger.log_file = log_file
    except Exception as e:
        root_logger.error(f"Could not configure file logging: {e}")
    
    # Log initial message
    root_logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    
    return root_logger
