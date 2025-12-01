import secrets
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Optional, Tuple
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_api_key() -> str:
    random_bytes = secrets.token_bytes(32)
    api_key = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return f"{settings.API_KEY_PREFIX}{api_key}"


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_signature(data: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(data: str, signature: str, secret: str) -> bool:
    expected_signature = generate_signature(data, secret)
    return hmac.compare_digest(signature, expected_signature)


def generate_transaction_id(prefix: str = "TXN") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4).upper()
    return f"{prefix}{timestamp}{random_part}"


def generate_reference_id(prefix: str = "REF") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(6).upper()
    return f"{prefix}{timestamp}{random_part}"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    if len(data) <= visible_chars * 2:
        return "*" * len(data)
    return data[:visible_chars] + "*" * (len(data) - visible_chars * 2) + data[-visible_chars:]


def sanitize_input(input_str: str) -> str:
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
    sanitized = input_str
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    cleaned = ''.join(filter(str.isdigit, phone))
    
    if len(cleaned) == 10:
        return True, cleaned
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        return True, cleaned[2:]
    elif len(cleaned) == 11 and cleaned.startswith('0'):
        return True, cleaned[1:]
    else:
        return False, phone


def validate_email(email: str) -> bool:
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_otp(length: int = 6) -> str:
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


class RateLimiter:
    def __init__(self):
        self._requests: dict = {}
    
    def is_allowed(self, client_id: str, limit: int = None, period: int = None) -> Tuple[bool, int]:
        limit = limit or settings.RATE_LIMIT_REQUESTS
        period = period or settings.RATE_LIMIT_PERIOD
        
        now = datetime.utcnow().timestamp()
        key = f"rate:{client_id}"
        
        if key not in self._requests:
            self._requests[key] = []
        
        self._requests[key] = [
            ts for ts in self._requests[key] 
            if now - ts < period
        ]
        
        if len(self._requests[key]) >= limit:
            remaining = int(period - (now - self._requests[key][0]))
            return False, remaining
        
        self._requests[key].append(now)
        return True, 0


rate_limiter = RateLimiter()
