"""
Tests for helper functions.
"""

import pytest
from src.utils.helpers import (
    format_duration,
    format_view_count,
    format_date,
    sanitize_filename,
    generate_id
)


def test_format_duration():
    """Test duration formatting."""
    assert format_duration(0) == "0:00"
    assert format_duration(45) == "0:45"
    assert format_duration(60) == "1:00"
    assert format_duration(90) == "1:30"
    assert format_duration(3600) == "1:00:00"
    assert format_duration(3661) == "1:01:01"
    assert format_duration(7325) == "2:02:05"


def test_format_view_count():
    """Test view count formatting."""
    assert format_view_count(0) == "0"
    assert format_view_count(500) == "500"
    assert format_view_count(999) == "999"
    assert format_view_count(1000) == "1.0K"
    assert format_view_count(1500) == "1.5K"
    assert format_view_count(9999) == "10.0K"
    assert format_view_count(1000000) == "1.0M"
    assert format_view_count(1500000) == "1.5M"
    assert format_view_count(1000000000) == "1.0B"
    assert format_view_count(1500000000) == "1.5B"


def test_format_date():
    """Test date formatting."""
    assert format_date("20230115") == "Jan 15, 2023"
    assert format_date("20231225") == "Dec 25, 2023"
    assert format_date("") == ""
    assert format_date("invalid") == "invalid"
    assert format_date("2023") == "2023"


def test_sanitize_filename():
    """Test filename sanitization."""
    assert sanitize_filename("normal_file.txt") == "normal_file.txt"
    assert sanitize_filename("file with spaces.txt") == "file_with_spaces.txt"
    assert sanitize_filename("file<with>invalid:chars.txt") == "filewithinvalidchars.txt"
    assert sanitize_filename("file|with?*stars.txt") == "filewithstars.txt"
    assert sanitize_filename("file\"with\"quotes.txt") == "filewithquotes.txt"
    assert sanitize_filename("file/with/slashes.txt") == "filewithslashes.txt"


def test_generate_id():
    """Test ID generation."""
    id1 = generate_id()
    id2 = generate_id()
    
    assert isinstance(id1, str)
    assert len(id1) == 8
    assert isinstance(id2, str)
    assert len(id2) == 8
    # IDs should be different (very unlikely to fail)
    assert id1 != id2
