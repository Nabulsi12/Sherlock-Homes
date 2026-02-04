"""
Custom Validators
"""

import re
from typing import Optional


def validate_ssn(ssn: str) -> bool:
    """Validate Social Security Number format"""
    pattern = r'^\d{3}-\d{2}-\d{4}$'
    return bool(re.match(pattern, ssn))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-numeric characters
    digits = re.sub(r'\D', '', phone)
    return len(digits) == 10 or len(digits) == 11


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_currency(value: str) -> float:
    """Convert currency string to float"""
    # Remove $ , and spaces
    cleaned = value.replace('$', '').replace(',', '').replace(' ', '')
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Invalid currency value: {value}")
