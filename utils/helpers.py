import re
from typing import Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format (international)"""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone) is not None

def validate_gstin(gstin: str) -> bool:
    """Validate GSTIN format (India)"""
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return re.match(pattern, gstin) is not None

def validate_pincode(pincode: str) -> bool:
    """Validate Indian pincode format"""
    pattern = r'^[1-9][0-9]{5}$'
    return re.match(pattern, pincode) is not None

def generate_uuid(prefix: str = "") -> str:
    """Generate UUID with optional prefix"""
    import uuid
    uuid_str = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{prefix}-{uuid_str}" if prefix else uuid_str

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat() if dt else None

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def sanitize_string(text: str) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    # Remove potentially harmful characters
    return re.sub(r'[<>"\']', '', text.strip())

def calculate_credit_usage_percentage(used: int, total: int) -> float:
    """Calculate credit usage percentage"""
    if total == 0:
        return 0.0
    return round((used / total) * 100, 2)

def is_valid_credit_amount(amount: int) -> bool:
    """Validate credit amount is positive and reasonable"""
    return isinstance(amount, int) and amount > 0 and amount <= 1000000
