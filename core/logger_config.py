# logger_config.py
import os
import logging
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "domain_analyzer.log")

def setup_logger(name: str) -> logging.Logger:
    """
    Configure a named logger with both file and console output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Or INFO in production

    # Avoid duplicate handlers
    if not logger.handlers:
        # Rotating file handler (5 MB max, keep 3 backups)
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console logger
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
