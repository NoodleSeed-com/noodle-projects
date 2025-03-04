"""
Validation fixtures for tests.

This module provides fixtures for validating API responses against schemas.
"""
import pytest
from typing import Dict, List, Any, Type, TypeVar, Optional, Union, Callable
from pydantic import BaseModel, TypeAdapter

from app.models.project import ProjectResponse, ProjectCreate, ProjectUpdate
from app.models.version import VersionResponse, VersionCreate
from app.models.file import FileResponse, FileCreate
from app.models.base import PaginatedResponse


T = TypeVar('T', bound=BaseModel)


@pytest.fixture
def validate_response():
    """
    Create a function for validating API responses against schemas.
    
    This fixture provides a function to validate API responses against
    Pydantic schemas, ensuring the response format is correct.
    
    Returns:
        callable: A function that validates API responses
    """
    def _validate(response_data: Any, schema_type: Type[T]) -> T:
        """
        Validate a response against a schema.
        
        Args:
            response_data: The data to validate
            schema_type: The Pydantic schema to validate against
            
        Returns:
            The validated data as a Pydantic model
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Handle collections
            if isinstance(response_data, list):
                adapter = TypeAdapter(List[schema_type])
                return adapter.validate_python(response_data)
            # Handle single objects
            return schema_type.model_validate(response_data)
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")
    
    return _validate


@pytest.fixture
def validate_paginated_response():
    """
    Create a function for validating paginated API responses.
    
    This fixture provides a function to validate paginated API responses,
    which have a specific format with total, items, skip, and limit.
    
    Returns:
        callable: A function that validates paginated responses
    """
    def _validate_paginated(response_data: Dict[str, Any], item_schema: Type[T]) -> List[T]:
        """
        Validate a paginated response.
        
        Args:
            response_data: The paginated response data
            item_schema: The schema for items in the response
            
        Returns:
            The validated items as a list of Pydantic models
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Create a generic paginated response type with the specific item type
            paginated_type = PaginatedResponse[item_schema]
            
            # Validate the response
            validated = paginated_type.model_validate(response_data)
            
            # Return the items
            return validated.items
        except Exception as e:
            raise ValueError(f"Pagination validation error: {str(e)}")
    
    return _validate_paginated


@pytest.fixture
def schema_validators(validate_response, validate_paginated_response):
    """
    Create a collection of schema validators for common types.
    
    This fixture provides pre-configured validators for common schema types
    used in the application, making it easier to validate responses in tests.
    
    Returns:
        dict: A dictionary of validator functions for different schemas
    """
    return {
        "project": lambda data: validate_response(data, ProjectResponse),
        "projects": lambda data: validate_paginated_response(data, ProjectResponse),
        "version": lambda data: validate_response(data, VersionResponse),
        "versions": lambda data: validate_paginated_response(data, VersionResponse),
        "file": lambda data: validate_response(data, FileResponse),
        "files": lambda data: validate_response(data, List[FileResponse])
    }