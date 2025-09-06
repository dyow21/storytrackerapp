"""
Configuration settings for the Story Tracker app
"""

import os
from pathlib import Path


class Settings:
    """Application settings and configuration"""

    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'story_tracker.db')

    # Scraping settings
    SCRAPER_BASE_URL = "https://storytracker.solutionsjournalism.org/"
    SCRAPER_DELAY = float(os.getenv('SCRAPER_DELAY', '0.5'))  # Delay between requests
    SCRAPER_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', '15'))  # Request timeout
    MAX_ARTICLES_PER_SCRAPE = int(os.getenv('MAX_ARTICLES_PER_SCRAPE', '50'))

    # Email settings
    EMAIL_OUTPUT_DIR = Path(os.getenv('EMAIL_OUTPUT_DIR', 'emails_output'))
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Solutions Story Tracker')
    EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'stories@example.edu')

    # Scheduling settings
    DEFAULT_SCHEDULE_DAY = int(os.getenv('DEFAULT_SCHEDULE_DAY', '1'))  # Tuesday
    DEFAULT_SCHEDULE_HOUR = int(os.getenv('DEFAULT_SCHEDULE_HOUR', '9'))  # 9 AM
    DEFAULT_SCHEDULE_MINUTE = int(os.getenv('DEFAULT_SCHEDULE_MINUTE', '0'))

    # Admin settings
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Article retention
    DEFAULT_ARTICLE_RETENTION_DAYS = int(os.getenv('ARTICLE_RETENTION_DAYS', '90'))

    # Rate limiting
    SCRAPER_USER_AGENT = os.getenv(
        'SCRAPER_USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )

    # App settings
    APP_NAME = "Story Tracker Newsletter"
    APP_VERSION = "1.0.0"
    DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

    # Streamlit settings
    STREAMLIT_CONFIG = {
        'page_title': APP_NAME,
        'page_icon': '📰',
        'layout': 'wide'
    }

    @classmethod
    def get_database_url(cls):
        """Get database connection URL"""
        return f"sqlite:///{cls.DATABASE_PATH}"

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.EMAIL_OUTPUT_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_email_schedule(cls):
        """Get default email schedule as dict"""
        return {
            'day': cls.DEFAULT_SCHEDULE_DAY,
            'hour': cls.DEFAULT_SCHEDULE_HOUR,
            'minute': cls.DEFAULT_SCHEDULE_MINUTE
        }


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG_MODE = True
    SCRAPER_DELAY = 1.0  # Slower in development


class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG_MODE = False
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # Must be set in production

    @classmethod
    def validate(cls):
        """Validate production settings"""
        if not cls.ADMIN_PASSWORD:
            raise ValueError("ADMIN_PASSWORD must be set in production")


# Get current settings based on environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

if ENVIRONMENT == 'production':
    current_settings = ProductionSettings()
else:
    current_settings = DevelopmentSettings()

# Ensure directories exist
current_settings.ensure_directories()