"""
Common error types for the application.
"""
from enum import Enum, auto

class ErrorType(Enum):
    """Types of errors that can occur in the application."""
    VALIDATION = auto()
    DATABASE = auto()
    NOT_FOUND = auto()
    PERMISSION = auto()
    SERVICE_ERROR = auto()  # For external service errors (OpenRouter, etc.)

class NoodleError(Exception):
    """Base error class for all application errors."""
    def __init__(self, message: str, error_type: ErrorType = ErrorType.VALIDATION):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)
