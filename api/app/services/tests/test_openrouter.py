"""Tests for OpenRouter service."""
import pytest
import asyncio
import os
import re
import json
import logging
from unittest.mock import Mock, patch, MagicMock, mock_open, AsyncMock, call
from pathlib import Path
from openai import AsyncOpenAI, OpenAIError, APITimeoutError, RateLimitError
from ...config import settings
from ...services.openrouter import OpenRouterService, _read_prompt_file
from ...models.file import FileResponse, FileChange, AIResponse

@pytest.mark.asyncio
async def test_get_file_changes_with_none_client():
    """Test get_file_changes when client is None."""
    # Create a mock client that returns None
    mock_client = AsyncMock()
    mock_client.chat = None
    service = OpenRouterService(client=mock_client)
    changes = await service.get_file_changes("test", "test", [])
    assert changes == []

def test_service_with_custom_client():
    """Test service initialization with custom client."""
    mock_client = AsyncMock()
    service = OpenRouterService(client=mock_client)
    assert service.client == mock_client
    assert service._client_initialized == True

@pytest.mark.asyncio
@patch('app.services.openrouter.AsyncOpenAI')
async def test_service_client_creation(mock_openai_class):
    """Test AsyncOpenAI client creation with correct configuration."""
    mock_client = AsyncMock()
    mock_openai_class.return_value = mock_client

    # Use monkeypatch instead of patch.dict to avoid side effects
    with patch.object(settings, 'OPENROUTER_API_KEY', 'test-key'):
        service = OpenRouterService()
        await service._ensure_client()
        
    assert service.client == mock_client
    mock_openai_class.assert_called_once_with(
        base_url="https://openrouter.ai/api/v1",
        api_key="test-key",
        default_headers={
            "HTTP-Referer": "https://noodleseed.com",
            "X-Title": "Noodle Seed"
        }
    )

@pytest.mark.asyncio
async def test_service_missing_api_key():
    """Test service creation without API key."""
    # Use monkeypatch instead of patch.dict to avoid side effects
    with patch.object(settings, 'OPENROUTER_API_KEY', None):
        service = OpenRouterService()
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
            await service._ensure_client()

@pytest.mark.asyncio
async def test_get_file_changes_success():
    """Test successful file changes request."""
    # Setup mock client and response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    # Test data
    project_context = "Test project"
    change_request = "Create a file"
    current_files = [
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            path="existing.txt",
            content="existing content"
        )
    ]
    
    # Execute and verify
    changes = await service.get_file_changes(project_context, change_request, current_files)
    
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert changes[0].content == "test"
    assert changes[0].operation == "create"
    
    # Verify client call
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "google/gemini-2.0-flash-001"
    assert len(call_args["messages"]) == 2
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][1]["role"] == "user"

@pytest.mark.asyncio
async def test_get_file_changes_multiple_operations():
    """Test file changes with multiple operations to ensure return value is properly handled."""
    # Setup mock client with multiple changes
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='''<noodle_response>
                {
                    "changes": [
                        {"operation": "create", "path": "new-file.txt", "content": "new content"},
                        {"operation": "update", "path": "existing.txt", "content": "updated content"},
                        {"operation": "delete", "path": "to-delete.txt", "content": ""}
                    ]
                }
                </noodle_response>'''
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify all changes are returned correctly
    assert len(changes) == 3
    
    # First change - create
    assert changes[0].operation == "create"
    assert changes[0].path == "new-file.txt"
    assert changes[0].content == "new content"
    
    # Second change - update
    assert changes[1].operation == "update"
    assert changes[1].path == "existing.txt"
    assert changes[1].content == "updated content"
    
    # Third change - delete
    assert changes[2].operation == "delete"
    assert changes[2].path == "to-delete.txt"
    assert changes[2].content == ""

@pytest.mark.asyncio
@patch('app.services.openrouter.AIResponse')
async def test_get_file_changes_return_value(mock_ai_response_class):
    """Test that get_file_changes returns the changes from AIResponse."""
    # Setup mock response
    mock_changes = [
        FileChange(operation="create", path="test.txt", content="test content")
    ]
    
    # Create a mock AIResponse instance
    mock_ai_response = MagicMock()
    mock_ai_response.changes = mock_changes
    
    # Make model_validate_json return our mock instance
    mock_ai_response_class.model_validate_json.return_value = mock_ai_response
    
    # Setup mock client
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test content"}]}</noodle_response>'
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    result = await service.get_file_changes("test", "test", [])
    
    # Verify AIResponse.model_validate_json was called
    mock_ai_response_class.model_validate_json.assert_called_once()
    
    # Verify the result is exactly the changes from our mock AIResponse
    assert result is mock_changes

@pytest.mark.asyncio
async def test_invalid_ai_response_missing_tags():
    """Test handling of AI response missing noodle_response tags."""
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content="Response without noodle_response tags"
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(ValueError, match="AI response missing noodle_response tags"):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_invalid_ai_response_invalid_json():
    """Test handling of invalid JSON in AI response."""
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"invalid": "json"</noodle_response>'
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(Exception) as exc_info:
        await service.get_file_changes("test", "test", [])
    assert "validation error" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_duplicate_file_paths():
    """Test handling of duplicate file paths in changes."""
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='''<noodle_response>
                {
                    "changes": [
                        {"operation": "create", "path": "test.txt", "content": "test1"},
                        {"operation": "update", "path": "test.txt", "content": "test2"}
                    ]
                }
                </noodle_response>'''
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(ValueError, match="Duplicate file paths found in changes"):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_openai_api_error():
    """Test handling of OpenAI API errors."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = OpenAIError("API Error")
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(OpenAIError, match="API Error"):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_openai_timeout():
    """Test handling of API timeouts."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = APITimeoutError("Request timed out")
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(APITimeoutError, match="timed out"):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_rate_limit_error():
    """Test handling of rate limit errors."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    
    error_body = {
        "error": {
            "message": "Rate limit exceeded",
            "type": "requests",
            "code": "rate_limit_exceeded"
        }
    }
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit exceeded",
        response=mock_response,
        body=error_body
    )
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(RateLimitError, match="Rate limit"):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_empty_response():
    """Test handling of empty response from OpenAI."""
    mock_completion = MagicMock()
    mock_completion.choices = []
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(IndexError):
        await service.get_file_changes("test", "test", [])

@pytest.mark.asyncio
async def test_missing_message_in_choice():
    """Test handling of missing message in choice."""
    mock_choice = MagicMock()
    del mock_choice.message
    
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    service = OpenRouterService(client=mock_client)
    
    with pytest.raises(AttributeError):
        await service.get_file_changes("test", "test", [])

def test_missing_prompt_file():
    """Test handling of missing prompt file."""
    with pytest.raises(FileNotFoundError):
        _read_prompt_file("nonexistent.md")

def test_read_prompt_file():
    """Test successful prompt file reading."""
    with patch('builtins.open', mock_open(read_data="test content")):
        content = _read_prompt_file("test.md")
        assert content == "test content"

@pytest.mark.asyncio
async def test_retry_successful_after_timeout():
    """Test that API call is retried after a timeout and succeeds on retry."""
    # Create a mock client that fails with timeout once, then succeeds
    mock_client = AsyncMock()
    
    # First call raises timeout error
    # Second call succeeds with valid response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    # Configure the side effect to fail once then succeed
    mock_client.chat.completions.create.side_effect = [
        APITimeoutError("Request timed out"),
        mock_completion
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Execute the method
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify result and that client method was called twice
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert mock_client.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_retry_successful_after_rate_limit():
    """Test that API call is retried after a rate limit error and succeeds on retry."""
    # Create a mock client
    mock_client = AsyncMock()
    
    # Configure mock response for rate limit error
    mock_response = MagicMock()
    mock_response.status_code = 429
    error_body = {
        "error": {
            "message": "Rate limit exceeded",
            "type": "requests",
            "code": "rate_limit_exceeded"
        }
    }
    
    # Configure successful response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    # Configure the side effect to fail with rate limit then succeed
    mock_client.chat.completions.create.side_effect = [
        RateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body=error_body
        ),
        mock_completion
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert mock_client.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_retry_successful_after_malformed_response():
    """Test that API call is retried after receiving a malformed response."""
    # Create a mock client
    mock_client = AsyncMock()
    
    # First response is malformed (missing tags)
    malformed_completion = MagicMock()
    malformed_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='Response without tags'
            )
        )
    ]
    
    # Second response is correct
    valid_completion = MagicMock()
    valid_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    # Configure mock to return malformed response first, then valid
    mock_client.chat.completions.create.side_effect = [
        malformed_completion,
        valid_completion
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert mock_client.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_retry_failed_after_max_attempts():
    """Test that API call fails after maximum retry attempts."""
    # Create a mock client that always fails with timeout
    mock_client = AsyncMock()
    
    # Configure mock to always fail with timeout
    mock_client.chat.completions.create.side_effect = APITimeoutError("Request timed out")
    
    service = OpenRouterService(client=mock_client)
    
    # Execute and expect failure after 3 attempts
    with pytest.raises(APITimeoutError, match="Request timed out"):
        await service.get_file_changes("test", "test", [])
    
    # Verify client was called exactly 3 times (initial + 2 retries)
    assert mock_client.chat.completions.create.call_count == 3

@pytest.mark.asyncio
async def test_retry_with_different_error_types():
    """Test retry with different types of errors in sequence."""
    # Create a mock client
    mock_client = AsyncMock()
    
    # Configure mock response for rate limit error
    mock_response = MagicMock()
    mock_response.status_code = 429
    error_body = {
        "error": {
            "message": "Rate limit exceeded",
            "type": "requests",
            "code": "rate_limit_exceeded"
        }
    }
    
    # Configure valid response for success
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    # Configure the mock to fail with different errors before succeeding
    mock_client.chat.completions.create.side_effect = [
        APITimeoutError("Request timed out"),  # First failure - timeout
        RateLimitError(                       # Second failure - rate limit
            message="Rate limit exceeded",
            response=mock_response,
            body=error_body
        ),
        mock_completion                       # Success on third try
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert mock_client.chat.completions.create.call_count == 3

@pytest.mark.asyncio
async def test_retry_with_invalid_json():
    """Test retry with invalid JSON in response."""
    # Create a mock client
    mock_client = AsyncMock()
    
    # First response has invalid JSON
    invalid_json_completion = MagicMock()
    invalid_json_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"invalid": json}</noodle_response>'
            )
        )
    ]
    
    # Second response is valid
    valid_completion = MagicMock()
    valid_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    # Configure mock
    mock_client.chat.completions.create.side_effect = [
        invalid_json_completion,
        valid_completion
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Execute
    changes = await service.get_file_changes("test", "test", [])
    
    # Verify
    assert len(changes) == 1
    assert changes[0].path == "test.txt"
    assert mock_client.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_retry_with_exponential_backoff():
    """Test that retry uses exponential backoff between attempts."""
    # Create a mock client that always fails
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = APITimeoutError("Request timed out")
    
    service = OpenRouterService(client=mock_client)
    
    # Mock the sleep function to track delays
    sleep_times = []
    
    async def mock_sleep(seconds):
        sleep_times.append(seconds)
        return
    
    # Patch asyncio.sleep to use our mock
    with patch('asyncio.sleep', mock_sleep):
        # Execute and expect failure after max retries
        with pytest.raises(APITimeoutError):
            await service.get_file_changes("test", "test", [])
    
    # Verify that sleep was called with increasing delays
    assert len(sleep_times) == 2  # Two retries means two sleeps
    assert sleep_times[0] < sleep_times[1]  # Verify increasing backoff

@pytest.mark.asyncio
async def test_retry_preserves_original_parameters():
    """Test that retry uses the same parameters as the original call."""
    # Create a mock client
    mock_client = AsyncMock()
    
    # First call fails, second succeeds
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": [{"operation": "create", "path": "test.txt", "content": "test"}]}</noodle_response>'
            )
        )
    ]
    
    mock_client.chat.completions.create.side_effect = [
        APITimeoutError("Request timed out"),
        mock_completion
    ]
    
    service = OpenRouterService(client=mock_client)
    
    # Test data
    project_context = "Test project"
    change_request = "Create a file"
    current_files = [
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            path="existing.txt",
            content="existing content"
        )
    ]
    
    # Execute
    await service.get_file_changes(project_context, change_request, current_files)
    
    # Get the call arguments from both calls
    first_call_args = mock_client.chat.completions.create.call_args_list[0][1]
    second_call_args = mock_client.chat.completions.create.call_args_list[1][1]
    
    # Verify both calls used identical parameters
    assert first_call_args["model"] == second_call_args["model"]
    assert first_call_args["messages"] == second_call_args["messages"]

@pytest.mark.asyncio
async def test_execute_with_retry_success_first_try():
    """Test _execute_with_retry succeeds on first try without retries."""
    service = OpenRouterService()
    
    # Create a mock function that succeeds immediately
    mock_func = AsyncMock(return_value="success")
    
    # Execute with retry
    result = await service._execute_with_retry(mock_func, "arg1", key="value")
    
    # Verify result and that function was called exactly once with correct args
    assert result == "success"
    mock_func.assert_called_once_with("arg1", key="value")

@pytest.mark.asyncio
async def test_execute_with_retry_custom_max_retries():
    """Test _execute_with_retry with custom max_retries value."""
    service = OpenRouterService()
    
    # Create a mock function that always fails
    mock_func = AsyncMock(side_effect=ValueError("Test error"))
    
    # Execute with custom max_retries=5
    with pytest.raises(ValueError):
        await service._execute_with_retry(mock_func, max_retries=5)
    
    # Verify function was called exactly 6 times (initial + 5 retries)
    assert mock_func.call_count == 6

@pytest.mark.asyncio
async def test_process_ai_response():
    """Test _process_ai_response correctly extracts and validates changes."""
    service = OpenRouterService()
    
    # Sample response with valid changes
    response_text = '''Some text before
    <noodle_response>
    {"changes": [{"operation": "create", "path": "test.txt", "content": "test content"}]}
    </noodle_response>
    Some text after'''
    
    # Process the response
    changes = await service._process_ai_response(response_text)
    
    # Verify changes are extracted correctly
    assert len(changes) == 1
    assert changes[0].operation == "create"
    assert changes[0].path == "test.txt"
    assert changes[0].content == "test content"

@pytest.mark.asyncio
async def test_process_ai_response_whitespace_handling():
    """Test _process_ai_response handles whitespace in tags correctly."""
    service = OpenRouterService()
    
    # Sample response with extra whitespace in tags
    response_text = '''<noodle_response>   
    {"changes": [{"operation": "create", "path": "test.txt", "content": "test content"}]}
       </noodle_response>'''
    
    # Process the response
    changes = await service._process_ai_response(response_text)
    
    # Verify changes are extracted correctly
    assert len(changes) == 1
    assert changes[0].path == "test.txt"

@pytest.mark.asyncio
async def test_get_client():
    """Test _get_client initializes AsyncOpenAI client correctly."""
    service = OpenRouterService()
    
    # Mock environment variable
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_api_key"}):
        client = await service._get_client()
    
    # Verify client configuration
    assert client.api_key == "test_api_key"
    # The URL might end with a trailing slash, so we check if one contains the other
    assert "https://openrouter.ai/api/v1" in str(client.base_url)
    assert client.default_headers["HTTP-Referer"] == "https://noodleseed.com"
    assert client.default_headers["X-Title"] == "Noodle Seed"

@pytest.mark.asyncio
async def test_get_client_empty_key():
    """Test _get_client raises error for empty API key."""
    service = OpenRouterService()
    
    # Mock environment with empty API key
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
            await service._get_client()

@pytest.mark.asyncio
@patch('app.services.openrouter._read_prompt_file')
async def test_get_file_changes_formats_messages_correctly(mock_read_prompt):
    """Test get_file_changes formats system and user messages correctly."""
    # Mock prompt file reads
    mock_read_prompt.side_effect = [
        "System message template",  # system_message.md
        "Project: {project_context}\nFiles: {current_files}\nRequest: {change_request}"  # user_message_template.md
    ]
    
    # Create mock completion and client
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='<noodle_response>{"changes": []}</noodle_response>'
            )
        )
    ]
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion
    
    # Create service with mock client
    service = OpenRouterService(client=mock_client)
    
    # Test data
    project_context = "Test project context"
    change_request = "Create a file"
    current_files = [
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174000",  # Valid UUID
            path="file1.txt", 
            content="Content 1"
        ),
        FileResponse(
            id="123e4567-e89b-12d3-a456-426614174001",  # Valid UUID
            path="file2.txt", 
            content="Content 2"
        )
    ]
    
    # Call get_file_changes
    await service.get_file_changes(project_context, change_request, current_files)
    
    # Verify prompt files were read
    mock_read_prompt.assert_has_calls([
        call("system_message.md"),
        call("user_message_template.md")
    ])
    
    # Verify API was called with correctly formatted messages
    call_args = mock_client.chat.completions.create.call_args[1]
    messages = call_args["messages"]
    
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System message template"
    
    assert messages[1]["role"] == "user"
    assert "Test project context" in messages[1]["content"]
    assert "Create a file" in messages[1]["content"]
    assert "file1.txt" in messages[1]["content"]
    assert "file2.txt" in messages[1]["content"]
    assert "Content 1" in messages[1]["content"]
    assert "Content 2" in messages[1]["content"]

@pytest.mark.asyncio
@patch('logging.warning')
@patch('logging.info')
async def test_execute_with_retry_logs_retries(mock_log_info, mock_log_warning):
    """Test that _execute_with_retry logs retry attempts."""
    service = OpenRouterService()
    
    # Create a mock function that fails once then succeeds
    mock_func = AsyncMock(side_effect=[
        APITimeoutError("Request timed out"),
        "success"
    ])
    
    # Execute with retry
    result = await service._execute_with_retry(mock_func)
    
    # Verify result
    assert result == "success"
    
    # Verify logging calls - use assert_called_once to avoid relying on exact message
    mock_log_warning.assert_called_once()
    assert "API error during request" in mock_log_warning.call_args[0][0]
    assert "Request timed out" in mock_log_warning.call_args[0][0]
    
    mock_log_info.assert_called_once()
    assert "Retrying request" in mock_log_info.call_args[0][0]

@pytest.mark.asyncio
@patch('logging.error')
async def test_execute_with_retry_logs_all_attempts_failed(mock_log_error):
    """Test that _execute_with_retry logs when all retry attempts fail."""
    service = OpenRouterService()
    
    # Create a mock function that always fails
    test_error = ValueError("Test error")
    mock_func = AsyncMock(side_effect=test_error)
    
    # Execute with retry and expect failure
    with pytest.raises(ValueError):
        await service._execute_with_retry(mock_func, max_retries=1)
    
    # Verify error logging
    mock_log_error.assert_called_with(
        "All retry attempts failed: Test error"
    )

@pytest.mark.asyncio
async def test_get_openrouter():
    """Test get_openrouter dependency function."""
    from ...services.openrouter import get_openrouter
    
    # Verify the function returns an instance of OpenRouterService
    service = await get_openrouter()
    assert isinstance(service, OpenRouterService)
