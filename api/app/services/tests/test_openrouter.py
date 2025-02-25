"""Tests for OpenRouter service."""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open, AsyncMock
from pathlib import Path
from openai import AsyncOpenAI, OpenAIError, APITimeoutError, RateLimitError
from ...services.openrouter import OpenRouterService, _read_prompt_file
from ...schemas.file import FileResponse
from ...schemas.common import FileChange, AIResponse

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

    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
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
    with patch.dict('os.environ', clear=True):
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
async def test_get_openrouter():
    """Test get_openrouter dependency function."""
    from ...services.openrouter import get_openrouter
    
    # Verify the function returns an instance of OpenRouterService
    service = await get_openrouter()
    assert isinstance(service, OpenRouterService)
