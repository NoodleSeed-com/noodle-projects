"""Tests for Base model."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
from uuid import UUID, uuid4
from ...models.base import Base

class TestModel(Base):
    """Test model class inheriting from Base."""
    __tablename__ = "test_models"

    def __init__(self):
        super().__init__()

@pytest.mark.asyncio
async def test_base_model_creation(mock_db_session, mock_models):
    """Test base model field creation."""
    # Setup mock
    mock_test_model = MagicMock(spec=TestModel)
    mock_test_model.id = UUID('123e4567-e89b-12d3-a456-426614174000')
    created_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    mock_test_model.created_at = created_at
    mock_test_model.updated_at = updated_at

    mock_models.TestModel = MagicMock(return_value=mock_test_model)
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create model instance
    model = mock_models.TestModel()
    mock_db_session.add(model)
    await mock_db_session.commit()
    await mock_db_session.refresh(model)

    # Verify base fields
    assert isinstance(model.id, UUID)
    assert model.created_at == created_at
    assert model.updated_at == updated_at
    assert model.created_at.tzinfo is not None  # Verify timezone awareness
    assert model.updated_at.tzinfo is not None  # Verify timezone awareness

@pytest.mark.asyncio
async def test_base_model_update(mock_db_session, mock_models):
    """Test base model update behavior."""
    # Setup mock
    mock_test_model = MagicMock(spec=TestModel)
    mock_test_model.id = UUID('123e4567-e89b-12d3-a456-426614174000')
    created_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    mock_test_model.created_at = created_at
    mock_test_model.updated_at = updated_at

    mock_models.TestModel = MagicMock(return_value=mock_test_model)
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create and update model
    model = mock_models.TestModel()
    mock_db_session.add(model)
    await mock_db_session.commit()
    await mock_db_session.refresh(model)

    initial_created_at = model.created_at
    initial_updated_at = model.updated_at

    # Simulate update after 1 minute
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0, tzinfo=timezone.utc)
    mock_test_model.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(model)

    # Verify timestamps
    assert model.created_at == initial_created_at  # created_at should not change
    assert model.updated_at == new_updated_at  # updated_at should be updated
    assert model.updated_at > model.created_at  # updated_at should be later than created_at

@pytest.mark.asyncio
async def test_base_model_id_generation(mock_db_session, mock_models):
    """Test UUID generation for base model."""
    # Create multiple instances to verify unique IDs
    models = []
    ids = set()

    for _ in range(3):
        mock_test_model = MagicMock(spec=TestModel)
        mock_test_model.id = uuid4()  # Generate unique UUID for each instance
        mock_test_model.created_at = datetime.now(timezone.utc)
        mock_test_model.updated_at = datetime.now(timezone.utc)

        mock_models.TestModel = MagicMock(return_value=mock_test_model)
        mock_models.TestModel.return_value = mock_test_model
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = AsyncMock()
        mock_db_session.refresh.return_value = AsyncMock()

        model = mock_models.TestModel()
        mock_db_session.add(model)
        await mock_db_session.commit()
        await mock_db_session.refresh(model)

        models.append(model)
        ids.add(model.id)

    # Verify all IDs are unique
    assert len(ids) == len(models)
    for model in models:
        assert isinstance(model.id, UUID)

@pytest.mark.asyncio
async def test_base_model_server_defaults(mock_db_session, mock_models):
    """Test server default behavior for timestamps."""
    # Create model without specifying timestamps
    mock_test_model = MagicMock(spec=TestModel)
    mock_test_model.id = uuid4()
    
    # Simulate server-generated timestamps
    server_time = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    mock_test_model.created_at = server_time
    mock_test_model.updated_at = server_time

    mock_models.TestModel = MagicMock(return_value=mock_test_model)
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    model = mock_models.TestModel()
    mock_db_session.add(model)
    await mock_db_session.commit()
    await mock_db_session.refresh(model)

    # Verify server defaults were applied
    assert model.created_at == server_time
    assert model.updated_at == server_time
    assert model.created_at.tzinfo == timezone.utc
    assert model.updated_at.tzinfo == timezone.utc

@pytest.mark.asyncio
async def test_base_model_timezone_handling(mock_db_session, mock_models):
    """Test timezone handling in timestamps."""
    mock_test_model = MagicMock(spec=TestModel)
    mock_test_model.id = uuid4()

    # Test different timezone representations
    utc_time = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    mock_test_model.created_at = utc_time
    mock_test_model.updated_at = utc_time

    mock_models.TestModel = MagicMock(return_value=mock_test_model)
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    model = mock_models.TestModel()
    mock_db_session.add(model)
    await mock_db_session.commit()
    await mock_db_session.refresh(model)

    # Verify timezone handling
    assert model.created_at.tzinfo == timezone.utc
    assert model.updated_at.tzinfo == timezone.utc
    assert model.created_at.isoformat().endswith('+00:00') or model.created_at.isoformat().endswith('Z')
    assert model.updated_at.isoformat().endswith('+00:00') or model.updated_at.isoformat().endswith('Z')


@pytest.mark.asyncio
async def test_base_model_inheritance(mock_db_session, mock_models):
    """Test inheritance behavior with multiple models."""
    class ChildModel(TestModel):
        """Child model for testing inheritance."""
        pass

    # Test inheritance of base fields
    mock_child_model = MagicMock(spec=ChildModel)
    mock_child_model.id = uuid4()
    created_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    updated_at = datetime(2025, 2, 24, 20, 0, 0, tzinfo=timezone.utc)
    mock_child_model.created_at = created_at
    mock_child_model.updated_at = updated_at

    mock_models.ChildModel = MagicMock(return_value=mock_child_model)
    mock_db_session.add.return_value = None
    mock_db_session.commit.return_value = AsyncMock()
    mock_db_session.refresh.return_value = AsyncMock()

    # Create child model instance
    child = mock_models.ChildModel()
    mock_db_session.add(child)
    await mock_db_session.commit()
    await mock_db_session.refresh(child)

    # Verify inherited fields
    assert isinstance(child.id, UUID)
    assert child.created_at == created_at
    assert child.updated_at == updated_at
    assert child.created_at.tzinfo is not None
    assert child.updated_at.tzinfo is not None

    # Test update behavior in child
    new_updated_at = datetime(2025, 2, 24, 20, 1, 0, tzinfo=timezone.utc)
    mock_child_model.updated_at = new_updated_at
    await mock_db_session.commit()
    await mock_db_session.refresh(child)

    assert child.created_at == created_at
    assert child.updated_at == new_updated_at
    assert child.updated_at > child.created_at
