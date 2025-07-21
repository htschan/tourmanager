import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name):
    """
    Creates a logger with the specified name and configuration.
    Logs will be written to both console and a file.
    
    Args:
        name (str): The name of the logger, typically __name__
        
    Returns:
        logging.Logger: The configured logger
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        # Fallback to current directory if there's an issue
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
    # Set global logging level - more verbose during debugging
    logging.basicConfig(level=logging.INFO)
    
    # Configure the logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (rotating to prevent large log files)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Don't propagate to root logger
        logger.propagate = False
    
    return logger
