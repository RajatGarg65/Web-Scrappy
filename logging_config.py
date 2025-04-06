import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('website_processing.log'),
                        logging.StreamHandler()  # Optional: to also output logs to the console
                    ])

# Get a logger instance
logger = logging.getLogger(__name__)

