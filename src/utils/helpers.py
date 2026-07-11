"""
Helper functions for formatting and utility operations.
"""

from datetime import timedelta
from typing import Optional


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "3:45", "1:23:45")
    """
    if seconds <= 0:
        return "0:00"
    
    td = timedelta(seconds=seconds)
    
    if td.total_seconds() >= 3600:
        # Hours:Minutes:Seconds
        return str(td)
    else:
        # Minutes:Seconds
        minutes = td.seconds // 60
        seconds = td.seconds % 60
        return f"{minutes}:{seconds:02d}"


def format_view_count(count: int) -> str:
    """
    Format view count to a human-readable string.
    
    Args:
        count: View count
    
    Returns:
        Formatted string (e.g., "1.2K", "1.5M", "2.3B")
    """
    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    elif count < 1_000_000_000:
        return f"{count / 1_000_000:.1f}M"
    else:
        return f"{count / 1_000_000_000:.1f}B"


def format_date(date_str: str) -> str:
    """
    Format a date string to a more readable format.
    
    Args:
        date_str: Date string (e.g., "20230115")
    
    Returns:
        Formatted date string (e.g., "Jan 15, 2023")
    """
    if not date_str or len(date_str) != 8:
        return date_str
    
    try:
        from datetime import datetime
        date = datetime.strptime(date_str, "%Y%m%d")
        return date.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: Input string
    
    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters including forward slashes
    sanitized = re.sub(r'[<>:"\|?*\x00-\x1f\/]', "", filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    return sanitized

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        Unique ID string
    """
    import uuid
    return uuid.uuid4().hex[:8]
