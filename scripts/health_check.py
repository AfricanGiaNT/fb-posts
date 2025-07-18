#!/usr/bin/env python3
"""
Health check script for Render deployment
"""

import os
import sys
import logging
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'OPENAI_API_KEY',
        'AIRTABLE_API_KEY',
        'AIRTABLE_BASE_ID',
        'AIRTABLE_TABLE_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("All required environment variables are set")
    return True

def check_config():
    """Check if configuration can be loaded."""
    try:
        config = ConfigManager()
        config.validate_config()
        logger.info("Configuration validation passed")
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def main():
    """Main health check function."""
    logger.info("Starting health check...")
    
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    logger.info("Health check passed")
    sys.exit(0)

if __name__ == "__main__":
    main() 