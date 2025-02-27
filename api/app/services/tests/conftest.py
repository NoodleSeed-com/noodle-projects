"""Test fixtures for services."""
import pytest
import asyncio
from unittest.mock import MagicMock

@pytest.fixture
def event_loop():
    """Create a new event loop for each test.
    
    This prevents issues with loop closure and ensures each test
    gets a fresh event loop instance.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='<noodle_response>{"changes": []}</noodle_response>'
                )
            )
        ]
    )
    return mock_client
