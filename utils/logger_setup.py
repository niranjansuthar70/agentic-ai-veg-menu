import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read environment and log level
env = os.getenv("ENV", "PROD").upper()
log_level = os.getenv("LOG_LEVEL", "DEBUG" if env == "DEBUG" else "INFO").upper()

# Configure logger
def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger configured based on environment.
    
    Args:
        name (str): Name of the logger (usually __name__).
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid adding multiple handlers in interactive environments
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # In PROD, reduce verbosity for third-party libs
    if env == "PROD":
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("google").setLevel(logging.WARNING)

    return logger
