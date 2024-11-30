import logging
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler("server.log", mode="a"),  # Output to a file
    ],
)

logger = logging.getLogger(
    "fastapi_server"
)  # Create a specific logger for the FastAPI app
