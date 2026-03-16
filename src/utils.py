import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {
        "airgradient_token": os.getenv("AIRGRADIENT_TOKEN", ""),
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
        "wachap_access_token": os.getenv("WACHAP_ACCESS_TOKEN", ""),
        "wachap_instance_id": os.getenv("WACHAP_INSTANCE_ID", ""),
        "database_url": os.getenv("DATABASE_URL", ""),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }
    return config

def validate_phone_number(phone: str) -> Optional[str]:
    """
    Validate and normalize a Senegalese phone number.

    :param phone: Phone number string
    :return: Normalized phone number or None if invalid
    """
    if not phone:
        return None

    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())

    # Handle different formats
    if digits.startswith('221') and len(digits) == 12:
        # Already in +221 format without +
        return f"+{digits}"
    elif digits.startswith('+221') and len(digits) == 13:
        # Already in +221 format with +
        return digits
    elif len(digits) == 9 and digits[0] in ('7', '3'):
        # Local format, add +221
        return f"+221{digits}"
    else:
        return None

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime to ISO string"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safely convert value to int"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0 if new_value == 0 else 100.0
    return ((new_value - old_value) / old_value) * 100.0

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_file_size_mb(filepath: str) -> float:
    """Get file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except OSError:
        return 0.0

def ensure_directory(path: str) -> None:
    """Ensure directory exists, create if necessary"""
    os.makedirs(path, exist_ok=True)

def clean_filename(filename: str) -> str:
    """Clean filename by removing invalid characters"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def generate_unique_id(prefix: str = "id") -> str:
    """Generate a unique ID with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}"

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
