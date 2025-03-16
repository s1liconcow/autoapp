import logging
from app.config.settings import settings

def setup_logger(name: str = __name__) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    
    # Set logging level based on development mode
    logger.setLevel(logging.DEBUG if settings.DEV_MODE else logging.INFO)
    
    # Create formatters
    dev_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    prod_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create handlers
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('llm_interactions.log')
    
    # Set formatters based on environment
    formatter = dev_formatter if settings.DEV_MODE else prod_formatter
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()
