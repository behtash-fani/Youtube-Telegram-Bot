import logging
from logging.handlers import RotatingFileHandler
import os

# Find the project root (2 levels up from this file)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create a rotating file handler
file_handler = RotatingFileHandler(
    LOG_FILE, 
    maxBytes=5 * 1024 * 1024,  # Max 5 MB per log file
    backupCount=3,            # Keep last 3 log files
    encoding="utf-8"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(message)s",
    handlers=[
        file_handler,           # Rotating file handler
        logging.StreamHandler() # Print logs to console
    ]
)

logger = logging.getLogger("app_logger")