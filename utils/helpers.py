"""
Utility functions and helpers for the Story Tracker app
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
import streamlit as st


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def clean_text(text: str) -> str:
    """
    Clean and normalize text content

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace and newlines
    text = ' '.join(text.split())

    # Remove common prefixes/suffixes that might appear in titles
    prefixes_to_remove = ['Story: ', 'Article: ', 'News: ', 'STORY: ']
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):]

    return text.strip()


def generate_url_hash(url: str) -> str:
    """
    Generate MD5 hash of URL for deduplication

    Args:
        url: URL to hash

    Returns:
        MD5 hash string
    """
    return hashlib.md5(url.encode()).hexdigest()


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL

    Args:
        url: URL to extract domain from

    Returns:
        Domain name or None if invalid URL
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain
    except Exception:
        return None


def format_outlet_name(domain: str) -> str:
    """
    Format outlet name from domain

    Args:
        domain: Domain name

    Returns:
        Formatted outlet name
    """
    if not domain:
        return "Unknown"

    # Remove domain extensions
    domain = domain.split('.')[0]

    # Handle known outlets
    outlet_mapping = {
        'nytimes': 'The New York Times',
        'washingtonpost': 'The Washington Post',
        'cnn': 'CNN',
        'bbc': 'BBC',
        'npr': 'NPR',
        'reuters': 'Reuters',
        'ap': 'Associated Press',
        'usatoday': 'USA Today',
        'theguardian': 'The Guardian',
        'wsj': 'The Wall Street Journal',
        'latimes': 'Los Angeles Times',
        'chicagotribune': 'Chicago Tribune',
        'seattletimes': 'The Seattle Times'
    }

    # Check if it's a known outlet
    if domain.lower() in outlet_mapping:
        return outlet_mapping[domain.lower()]

    # Otherwise, capitalize and clean up
    return domain.replace('-', ' ').replace('_', ' ').title()


def format_datetime(dt: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime object or ISO string

    Args:
        dt: Datetime object or ISO string
        format_str: Format string for output

    Returns:
        Formatted datetime string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt

    if isinstance(dt, datetime):
        return dt.strftime(format_str)

    return str(dt)


def time_ago(dt: Union[datetime, str]) -> str:
    """
    Get human-readable time ago string

    Args:
        dt: Datetime object or ISO string

    Returns:
        Human-readable time ago string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt

    if not isinstance(dt, datetime):
        return "Unknown"

    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def get_next_weekday(weekday: int, hour: int = 9, minute: int = 0) -> datetime:
    """
    Get next occurrence of specified weekday and time

    Args:
        weekday: Day of week (0=Monday, 6=Sunday)
        hour: Hour of day (0-23)
        minute: Minute of hour (0-59)

    Returns:
        Next datetime for specified weekday and time
    """
    now = datetime.now()
    days_ahead = weekday - now.weekday()

    if days_ahead <= 0:  # Target day has passed this week
        days_ahead += 7

    next_date = now + timedelta(days=days_ahead)
    next_date = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If it's the same day but time has passed, add a week
    if next_date <= now:
        next_date += timedelta(weeks=1)

    return next_date


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def safe_filename(filename: str) -> str:
    """
    Create safe filename by removing/replacing invalid characters

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[_\s]+', '_', filename)

    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')

    return filename


def create_error_message(error: Exception, context: str = "") -> str:
    """
    Create user-friendly error message

    Args:
        error: Exception object
        context: Additional context about where error occurred

    Returns:
        Formatted error message
    """
    base_message = f"An error occurred"
    if context:
        base_message += f" while {context}"

    error_detail = str(error)
    if error_detail and error_detail != "":
        base_message += f": {error_detail}"

    return base_message


def batch_process(items: List, batch_size: int = 10):
    """
    Generator to process items in batches

    Args:
        items: List of items to process
        batch_size: Size of each batch

    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def show_success_message(message: str, details: Optional[Dict] = None):
    """
    Show success message in Streamlit

    Args:
        message: Success message
        details: Optional details to display
    """
    st.success(f"✅ {message}")

    if details:
        with st.expander("Details"):
            for key, value in details.items():
                st.write(f"**{key}:** {value}")


def show_error_message(message: str, error: Optional[Exception] = None):
    """
    Show error message in Streamlit

    Args:
        message: Error message
        error: Optional exception object
    """
    st.error(f"❌ {message}")

    if error and st.checkbox("Show technical details"):
        st.code(str(error))


def show_info_message(message: str, icon: str = "ℹ️"):
    """
    Show info message in Streamlit

    Args:
        message: Info message
        icon: Icon to display
    """
    st.info(f"{icon} {message}")


def format_subscriber_count(count: int) -> str:
    """
    Format subscriber count with appropriate pluralization

    Args:
        count: Number of subscribers

    Returns:
        Formatted string
    """
    if count == 0:
        return "No subscribers"
    elif count == 1:
        return "1 subscriber"
    else:
        return f"{count:,} subscribers"


def format_article_count(count: int) -> str:
    """
    Format article count with appropriate pluralization

    Args:
        count: Number of articles

    Returns:
        Formatted string
    """
    if count == 0:
        return "No articles"
    elif count == 1:
        return "1 article"
    else:
        return f"{count:,} articles"


def get_weekday_name(weekday: int) -> str:
    """
    Get weekday name from number

    Args:
        weekday: Day of week (0=Monday, 6=Sunday)

    Returns:
        Weekday name
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[weekday] if 0 <= weekday <= 6 else 'Unknown'


def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """
    Create download link for data

    Args:
        data: Data to download
        filename: Filename for download
        mime_type: MIME type

    Returns:
        Download button in Streamlit
    """
    return st.download_button(
        label=f"📄 Download {filename}",
        data=data,
        file_name=filename,
        mime=mime_type
    )


def validate_settings(settings: Dict) -> List[str]:
    """
    Validate application settings

    Args:
        settings: Settings dictionary

    Returns:
        List of validation errors
    """
    errors = []

    # Validate email schedule
    if 'email_schedule_day' in settings:
        try:
            day = int(settings['email_schedule_day'])
            if not 0 <= day <= 6:
                errors.append("Email schedule day must be 0-6 (Monday-Sunday)")
        except ValueError:
            errors.append("Email schedule day must be a number")

    if 'email_schedule_hour' in settings:
        try:
            hour = int(settings['email_schedule_hour'])
            if not 0 <= hour <= 23:
                errors.append("Email schedule hour must be 0-23")
        except ValueError:
            errors.append("Email schedule hour must be a number")

    if 'email_schedule_minute' in settings:
        try:
            minute = int(settings['email_schedule_minute'])
            if not 0 <= minute <= 59:
                errors.append("Email schedule minute must be 0-59")
        except ValueError:
            errors.append("Email schedule minute must be a number")

    # Validate retention settings
    if 'article_retention_days' in settings:
        try:
            days = int(settings['article_retention_days'])
            if days < 1:
                errors.append("Article retention days must be at least 1")
        except ValueError:
            errors.append("Article retention days must be a number")

    return errors


class ProgressTracker:
    """Simple progress tracker for long-running operations"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()

    def update(self, increment: int = 1, status: str = None):
        """Update progress"""
        self.current += increment
        progress = min(self.current / self.total, 1.0)
        self.progress_bar.progress(progress)

        if status:
            self.status_text.text(f"{self.description}: {status}")
        else:
            self.status_text.text(f"{self.description}: {self.current}/{self.total}")

    def complete(self, message: str = "Complete"):
        """Mark as complete"""
        self.progress_bar.progress(1.0)
        self.status_text.text(message)


def export_to_csv(data: List[Dict], filename: str = None) -> str:
    """
    Export data to CSV format

    Args:
        data: List of dictionaries to export
        filename: Optional filename

    Returns:
        CSV string
    """
    import pandas as pd

    if not data:
        return ""

    df = pd.DataFrame(data)
    return df.to_csv(index=False)