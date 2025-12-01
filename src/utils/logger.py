import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from functools import wraps
import traceback

from src.config.settings import settings


class BBPSLogger:
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str = "bbps_proxy") -> logging.Logger:
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
            
            if not logger.handlers:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
                
                formatter = logging.Formatter(settings.LOG_FORMAT)
                console_handler.setFormatter(formatter)
                
                logger.addHandler(console_handler)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]


logger = BBPSLogger.get_logger()


def log_request(
    category: str,
    endpoint: str,
    method: str,
    request_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> str:
    request_id = f"{category}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    
    log_data: Dict[str, Any] = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "category": category,
        "endpoint": endpoint,
        "method": method,
        "type": "REQUEST"
    }
    
    if request_data:
        safe_data = {k: v for k, v in request_data.items() if k.lower() not in ["password", "pin", "otp", "cvv"]}
        log_data["payload"] = safe_data
    
    logger.info(f"BBPS Request: {json.dumps(log_data)}")
    return request_id


def log_response(
    request_id: str,
    category: str,
    status_code: int,
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None
) -> None:
    log_data = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "category": category,
        "status_code": status_code,
        "type": "RESPONSE"
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    if error:
        log_data["error"] = error
        logger.error(f"BBPS Response Error: {json.dumps(log_data)}")
    else:
        if response_data:
            log_data["response_summary"] = {
                "success": response_data.get("success", False),
                "message": response_data.get("message", "")
            }
        logger.info(f"BBPS Response: {json.dumps(log_data)}")


def log_error(
    category: str,
    endpoint: str,
    error: Exception,
    request_id: Optional[str] = None
) -> None:
    log_data = {
        "request_id": request_id or "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "category": category,
        "endpoint": endpoint,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "type": "ERROR"
    }
    
    logger.error(f"BBPS Error: {json.dumps(log_data)}")
