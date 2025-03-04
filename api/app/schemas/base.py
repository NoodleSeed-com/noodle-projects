"""
Base Pydantic schema imported from app.models.base.
This file re-exports BaseSchema to maintain backward compatibility.
"""
from app.models.base import BaseSchema

__all__ = ["BaseSchema"]
