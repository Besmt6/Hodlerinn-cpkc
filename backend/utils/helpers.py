"""
Utility Functions Module
Contains shared helper functions used across the application.
"""
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple


def calculate_stay_duration(
    check_in_date: str, 
    check_in_time: str, 
    check_out_date: str, 
    check_out_time: str
) -> Tuple[Optional[float], Optional[int]]:
    """
    Calculate total hours and nights billed based on 24-hour periods.
    
    Billing logic: 
    - Count based on 24-hour periods, not calendar days
    - Example: 28 hours = 2 nights (ceil(28/24) = 2)
    - Example: 23 hours = 1 night
    - Example: 48 hours = 2 nights
    - Example: 49 hours = 3 nights
    - Minimum 1 night for any stay
    
    Args:
        check_in_date: Date in YYYY-MM-DD format
        check_in_time: Time in HH:MM format
        check_out_date: Date in YYYY-MM-DD format
        check_out_time: Time in HH:MM format
    
    Returns:
        Tuple of (total_hours, total_nights) or (None, None) on error
    """
    try:
        check_in_dt = datetime.strptime(f"{check_in_date} {check_in_time}", "%Y-%m-%d %H:%M")
        check_out_dt = datetime.strptime(f"{check_out_date} {check_out_time}", "%Y-%m-%d %H:%M")
        
        duration = check_out_dt - check_in_dt
        total_hours = duration.total_seconds() / 3600
        
        # Billing logic: Count 24-hour periods (rounded up)
        total_nights = math.ceil(total_hours / 24)
        
        # Minimum 1 night for any stay
        if total_nights < 1:
            total_nights = 1
        
        return round(total_hours, 2), total_nights
    except Exception:
        return None, None


def get_central_time() -> datetime:
    """Get current time in US Central timezone"""
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo('America/Chicago'))


def format_date_for_display(date_str: str) -> str:
    """Format a date string for user-friendly display"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%b %d, %Y")  # e.g., "Mar 07, 2026"
    except:
        return date_str


def format_time_for_display(time_str: str) -> str:
    """Format a time string for user-friendly display"""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return time_obj.strftime("%I:%M %p")  # e.g., "02:30 PM"
    except:
        return time_str


def get_date_range(start_date: str, end_date: str) -> list:
    """Get a list of dates between start and end (inclusive)"""
    dates = []
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    except:
        pass
    return dates


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system use"""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized or "unnamed"


def generate_unique_id() -> str:
    """Generate a unique identifier"""
    import uuid
    return str(uuid.uuid4())


def parse_employee_name(name: str) -> Tuple[str, str]:
    """
    Parse employee name from format "LASTNAME,(FIRSTNAME)*CODE" 
    
    Args:
        name: Employee name string
    
    Returns:
        Tuple of (first_name, last_name)
    """
    import re
    name_match = re.match(r'([^,]+),?\(?([^)]*)\)?(?:\*\w+)?', name)
    if name_match:
        last_name = name_match.group(1).strip()
        first_name = name_match.group(2).strip() if name_match.group(2) else ""
    else:
        last_name = name
        first_name = ""
    return first_name, last_name
