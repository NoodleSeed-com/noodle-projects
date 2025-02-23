"""Tests for OpenRouter service."""
import pytest
from app.services.openrouter import OpenRouterService
from app.models.project import FileResponse

def test_openrouter_gemini(monkeypatch):
    """Test OpenRouter service with Gemini model."""
    # Create service instance
    service = OpenRouterService()
    
    # Mock environment variables
    monkeypatch.setenv("OPENROUTER_API_KEY", "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")
    monkeypatch.delenv("TESTING", raising=False)
    
    # Test data
    project_context = "This is a React TypeScript project."
    change_request = "Create a new Button component with primary and secondary variants."
    current_files = [
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            path="src/components/HelloWorld.tsx",
            content="""
import React from 'react';

const HelloWorld: React.FC = () => {
    return <h1>Hello, World!</h1>;
};

export default HelloWorld;
"""
        )
    ]
    
    # Get file changes
    changes = service.get_file_changes(project_context, change_request, current_files)
    
    # Verify response structure
    assert isinstance(changes, list), "Expected list of changes"
    for change in changes:
        assert hasattr(change, "operation"), "Change missing operation"
        assert hasattr(change, "path"), "Change missing path"
        assert hasattr(change, "content"), "Change missing content"
        assert change.operation in ["create", "update", "delete"], f"Invalid operation: {change.operation}"
        assert isinstance(change.path, str), "Path should be string"
        assert isinstance(change.content, str), "Content should be string"

def test_openrouter_testing_mode():
    """Test OpenRouter service in testing mode."""
    # Set TESTING environment variable
    service = OpenRouterService()
    
    # Service should return empty list in testing mode
    changes = service.get_file_changes("test", "test", [])
    assert changes == [], "Expected empty list in testing mode"

def test_openrouter_missing_key(monkeypatch):
    """Test OpenRouter service with missing API key."""
    # Remove the API key from environment
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("TESTING", raising=False)
    
    with pytest.raises(ValueError) as exc_info:
        service = OpenRouterService()
        service._get_client()
    assert "OPENROUTER_API_KEY environment variable is required" in str(exc_info.value)
