"""Structured logging with correlation IDs for request tracking"""
import logging
import sys
import json
from datetime import datetime
from contextvars import ContextVar
from typing import Optional

# Tracks correlation ID across async contexts
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class JSONFormatter(logging.Formatter):
    """Formats logs as JSON for easy parsing"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': correlation_id.get(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

def setup_logging(service_name: str, level: str = "INFO"):
    """Setup structured logging for a service"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    return logger

def set_correlation_id(corr_id: str):
    """Set correlation ID for request tracking"""
    correlation_id.set(corr_id)

def get_correlation_id() -> Optional[str]:
    """Get current correlation ID"""
    return correlation_id.get()
