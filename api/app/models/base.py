"""
Base models module providing common functionality for all models.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any, TypeVar, Generic, Type, Union, Callable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer, model_validator, ValidationError

from app.errors import NoodleError, ErrorType

# Type variable for generic model operations
T = TypeVar('T', bound='BaseSchema')

class BaseSchema(BaseModel):
    """Base class for all Pydantic models."""
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',  # Ignore extra fields when validating
        populate_by_name=True,  # Allow populating by both alias and field name
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-02-22T12:00:00Z",
                "updated_at": "2024-02-22T12:00:00Z"
            }
        }
    )
    
    @field_serializer('created_at', 'updated_at', when_used='json')
    def serialize_datetime(self, dt: datetime) -> str:
        """Serialize datetime fields to ISO format string."""
        return dt.isoformat() if dt else None

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a model instance from a dictionary.
        
        Args:
            data: The dictionary containing data
            
        Returns:
            An instance of the model class
            
        Raises:
            NoodleError: If the data is invalid for the model
        """
        if not data:
            return None
            
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            raise NoodleError(
                f"Invalid data for {cls.__name__}: {str(e)}", 
                ErrorType.VALIDATION
            )

    @classmethod
    def from_list(cls: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create a list of model instances from a list of dictionaries.
        
        Args:
            data_list: List of dictionaries
            
        Returns:
            List of model instances
        """
        if not data_list:
            return []
            
        return [cls.from_dict(item) for item in data_list]
    
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Convert model to dictionary, with option to exclude None values.
        
        Args:
            exclude_none: Whether to exclude fields with None values
            
        Returns:
            Dictionary representation of the model
        """
        return self.model_dump(exclude_none=exclude_none)

class SupabaseResponse(BaseModel):
    """Base class for Supabase response handling."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    def raise_for_error(self):
        """
        Raise an appropriate error if the response is not successful.
        
        Raises:
            NoodleError: With appropriate error type based on error_type field
        """
        if not self.success:
            error_type = ErrorType.DATABASE  # Default error type
            
            # Map Supabase error types to our application error types
            if self.error_type == "NOT_FOUND":
                error_type = ErrorType.NOT_FOUND
            elif self.error_type == "FORBIDDEN":
                error_type = ErrorType.PERMISSION
                
            raise NoodleError(self.error or "Unknown database error", error_type)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupabaseResponse':
        """
        Create a SupabaseResponse from a dictionary.
        
        Args:
            data: Dictionary with response data
            
        Returns:
            SupabaseResponse instance
        """
        return cls.model_validate(data)
    
    def to_model(self, model_class: Type[T]) -> T:
        """
        Convert the response data to a model instance.
        
        Args:
            model_class: The model class to convert to
            
        Returns:
            An instance of the model class
            
        Raises:
            NoodleError: If the response is not successful or data is invalid
        """
        self.raise_for_error()
        
        if not self.data:
            raise NoodleError("No data in successful response", ErrorType.DATABASE)
            
        return model_class.from_dict(self.data)
    
    def to_model_list(self, model_class: Type[T]) -> List[T]:
        """
        Convert the response data to a list of model instances.
        
        Args:
            model_class: The model class to convert to
            
        Returns:
            List of model instances
            
        Raises:
            NoodleError: If the response is not successful
        """
        self.raise_for_error()
        
        if not self.data or not isinstance(self.data, dict) or "items" not in self.data:
            return []
            
        return model_class.from_list(self.data["items"])

class PaginatedResponse(Generic[T]):
    """
    Generic class for paginated responses.
    
    Attributes:
        items: List of items in the current page
        total: Total number of items across all pages
        skip: Number of items skipped (offset)
        limit: Maximum number of items per page
    """
    def __init__(
        self, 
        items: List[T], 
        total: int, 
        skip: int = 0, 
        limit: int = 100
    ):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
    
    @classmethod
    def from_supabase(
        cls, 
        response: SupabaseResponse, 
        model_class: Type[T]
    ) -> 'PaginatedResponse[T]':
        """
        Create a PaginatedResponse from a Supabase response.
        
        Args:
            response: SupabaseResponse instance
            model_class: Model class for items
            
        Returns:
            PaginatedResponse instance
        """
        response.raise_for_error()
        
        if not response.data or not isinstance(response.data, dict):
            return cls([], 0, 0, 100)
            
        data = response.data
        items = model_class.from_list(data.get("items", []))
        total = data.get("total", len(items))
        skip = data.get("skip", 0)
        limit = data.get("limit", 100)
        
        return cls(items, total, skip, limit)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with pagination data
        """
        return {
            "items": [item.to_dict() if hasattr(item, "to_dict") else item for item in self.items],
            "total": self.total,
            "skip": self.skip,
            "limit": self.limit
        }

def generate_uuid() -> UUID:
    """
    Generate a new UUID.
    
    Returns:
        New UUID
    """
    return uuid4()

def dict_to_model(data: Dict[str, Any], model_class: Type[T]) -> Optional[T]:
    """
    Convert a dictionary to a model instance by utilizing Pydantic.
    This is useful for converting Supabase responses to our model objects.
    
    Args:
        data: The dictionary containing data
        model_class: The model class to convert to
        
    Returns:
        An instance of the model class
    """
    if not data:
        return None
    
    try:    
        # Use Pydantic to validate and convert
        return model_class.model_validate(data)
    except ValidationError as e:
        raise NoodleError(
            f"Invalid data for {model_class.__name__}: {str(e)}", 
            ErrorType.VALIDATION
        )

def handle_supabase_response(response: Dict[str, Any], model_class: Optional[Type[T]] = None) -> Union[T, Dict[str, Any]]:
    """
    Handle a Supabase response and convert to a model instance if model_class is provided.
    
    Args:
        response: Raw response dictionary from Supabase
        model_class: Optional model class to convert data to
        
    Returns:
        Model instance or raw response data
        
    Raises:
        NoodleError: If response indicates an error
    """
    supabase_response = SupabaseResponse.from_dict(response)
    
    if model_class:
        return supabase_response.to_model(model_class)
        
    return response["data"] if supabase_response.success else supabase_response.raise_for_error()
