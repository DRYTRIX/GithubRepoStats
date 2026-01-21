"""Utility functions for GitHub stats application."""

from datetime import datetime, timezone
from typing import Optional


def format_number(num: int) -> str:
    """Format large numbers with K/M suffixes for display."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_relative_time(dt: Optional[datetime]) -> str:
    """Format datetime as relative time (e.g., '2h ago', '3d ago')."""
    if dt is None:
        return "Never"
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    delta = now - dt
    
    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime as absolute time string."""
    if dt is None:
        return "Never"
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime("%Y-%m-%d %H:%M")


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO 8601 datetime string to datetime object."""
    # Handle various ISO formats
    for fmt in [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]:
        try:
            return datetime.strptime(iso_string, fmt)
        except ValueError:
            continue
    
    # Fallback to parsing with dateutil-like logic
    try:
        # Remove timezone info and parse
        dt_str = iso_string.replace("Z", "+00:00")
        if "+" in dt_str or dt_str.count("-") > 2:
            # Has timezone
            if dt_str.count(":") >= 3:
                # Has microseconds
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z")
        else:
            # No timezone
            if "." in dt_str:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
            else:
                return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        # Last resort: try basic format
        return datetime.strptime(iso_string[:19], "%Y-%m-%dT%H:%M:%S")
