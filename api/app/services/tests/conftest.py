"""Test fixtures for services."""
import pytest
from unittest.mock import MagicMock

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
