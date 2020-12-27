import logging
import config

logging.basicConfig(level=config.logging_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def getLogger(name):
    logger = logging.getLogger(name)
    return logger
