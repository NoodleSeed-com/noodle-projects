"""Tests for OpenRouter service."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.services.openrouter import OpenRouterService, _read_prompt_file
from app.models.project import FileResponse, FileOperation, FileChange
from pathlib import Path
from openai import OpenAIError, APITimeoutError, RateLimitError

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

def test_invalid_ai_response_missing_tags(monkeypatch):
    """Test handling of AI response missing noodle_response tags."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Mock OpenAI client
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content="Response without noodle_response tags"
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(ValueError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "AI response missing noodle_response tags" in str(exc_info.value)

def test_invalid_ai_response_invalid_json(monkeypatch):
    """Test handling of invalid JSON in AI response."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Mock OpenAI client with invalid JSON response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"invalid": "json"</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(Exception) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "validation error" in str(exc_info.value).lower()

def test_missing_prompt_file():
    """Test handling of missing prompt file."""
    with pytest.raises(FileNotFoundError):
        _read_prompt_file("nonexistent.md")

def test_empty_inputs(monkeypatch):
    """Test handling of empty inputs."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Mock successful response for empty inputs
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": []}</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        # Test empty project context
        changes = service.get_file_changes("", "test request", [])
        assert isinstance(changes, list)
        assert len(changes) == 0
        
        # Test empty change request
        changes = service.get_file_changes("test context", "", [])
        assert isinstance(changes, list)
        assert len(changes) == 0
        
        # Test empty files list
        changes = service.get_file_changes("test context", "test request", [])
        assert isinstance(changes, list)
        assert len(changes) == 0

def test_special_characters_in_paths(monkeypatch):
    """Test handling of special characters in file paths."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Mock response with special characters in paths
    special_path = "src/components/Special & Chars #1.tsx"
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content=f'<noodle_response>{{"changes": [{{"operation": "create", "path": "{special_path}", "content": "test"}}]}}</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        changes = service.get_file_changes("test", "test", [])
        assert len(changes) == 1
        assert changes[0].path == special_path

def test_large_file_content(monkeypatch):
    """Test handling of large file content."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Create a large file content (100KB)
    large_content = "x" * 100_000
    current_files = [
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174000",  # Valid UUID format
            path="large-file.txt",
            content=large_content
        )
    ]
    
    # Mock successful response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "update", "path": "large-file.txt", "content": "updated"}]}</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        # Should handle large file content without errors
        changes = service.get_file_changes("test", "test", current_files)
        assert len(changes) == 1
        assert changes[0].path == "large-file.txt"

def test_openai_api_error(monkeypatch):
    """Test handling of OpenAI API errors."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = OpenAIError("API Error")
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(OpenAIError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "API Error" in str(exc_info.value)

def test_openai_timeout(monkeypatch):
    """Test handling of API timeouts."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APITimeoutError("Request timed out")
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(APITimeoutError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "timed out" in str(exc_info.value)

def test_rate_limit_error(monkeypatch):
    """Test handling of rate limit errors."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Create mock HTTP response with rate limit status
    mock_response = MagicMock()
    mock_response.status_code = 429  # HTTP Too Many Requests
    
    # Construct valid RateLimitError with required parameters
    error_body = {
        "error": {
            "message": "Rate limit exceeded",
            "type": "requests",
            "code": "rate_limit_exceeded"
        }
    }
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body=error_body
        )
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(RateLimitError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "Rate limit" in str(exc_info.value)

def test_empty_response(monkeypatch):
    """Test handling of empty response from OpenAI."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    mock_completion = MagicMock()
    mock_completion.choices = []  # Empty choices list
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(IndexError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "list index out of range" in str(exc_info.value)

def test_missing_message_in_choice(monkeypatch):
    """Test handling of missing message in choice."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    # Create a mock choice that will raise AttributeError when accessing message
    mock_choice = MagicMock()
    del mock_choice.message  # This ensures accessing .message raises AttributeError
    
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(AttributeError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "message" in str(exc_info.value)

def test_invalid_operation_type(monkeypatch):
    """Test handling of invalid operation type in changes."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "invalid", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(ValueError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "operation" in str(exc_info.value).lower()

def test_duplicate_file_paths(monkeypatch):
    """Test handling of duplicate file paths in changes."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test1"}, {"operation": "update", "path": "test.txt", "content": "test2"}]}</noodle_response>'
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        with pytest.raises(ValueError) as exc_info:
            service.get_file_changes("test", "test", [])
        assert "duplicate" in str(exc_info.value).lower()

def test_nested_file_paths(monkeypatch):
    """Test handling of nested file paths."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TESTING", "false")
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='''<noodle_response>
                {
                    "changes": [
                        {"operation": "create", "path": "deeply/nested/path/file.txt", "content": "test"}
                    ]
                }
                </noodle_response>'''
            )
        )
    ]
    
    with patch('app.services.openrouter.OpenRouterService._get_client', autospec=True) as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_get_client.return_value = mock_client
        
        service = OpenRouterService()
        
        changes = service.get_file_changes("test", "test", [])
        assert len(changes) == 1
        assert changes[0].path == "deeply/nested/path/file.txt"
        assert changes[0].content == "test"
