"""
Example integration test demonstrating best practices.

This file shows how to structure integration tests with proper
fixtures, schema validation, and database operations.
"""
import pytest
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.sql import text

from app.models.project import ProjectCreate, ProjectResponse, Project
from app.crud.project import ProjectCRUD
from app.models.base import Base


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Database fixture needs further work")
async def test_create_and_retrieve_project(test_engine, db_session, create_payload, validate_response):
    """Test creating a project and retrieving it from the database."""
    # Verify the database has the required tables
    async with test_engine.begin() as conn:
        # For PostgreSQL, check if projects table exists
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'projects')"
        ))
        table_exists = result.scalar_one()
        if not table_exists:
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
    
    # Arrange - Prepare test data using fixture
    payload = create_payload("project", name="Integration Test Project")
    project_data = ProjectCreate(**payload)
    
    # Act - Create the project
    created_project = await ProjectCRUD.create(db=db_session, project=project_data)
    
    # Assert - Verify project was created correctly
    assert created_project.name == "Integration Test Project"
    assert isinstance(created_project.id, UUID)
    
    # Act - Retrieve the project
    retrieved_project = await ProjectCRUD.get(db=db_session, project_id=created_project.id)
    
    # Assert - Verify the project can be retrieved and matches
    assert retrieved_project is not None
    assert retrieved_project.id == created_project.id
    assert retrieved_project.name == created_project.name
    
    # Validate against schema
    validated = validate_response(created_project.model_dump(), ProjectResponse)
    assert validated.name == "Integration Test Project"


@pytest.mark.skip(reason="API client fixture not fully implemented yet")
@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_project_endpoint(async_client, db_session, create_payload, schema_validators):
    """Test the project API endpoint with schema validation."""
    # Arrange - Create a project in the database
    payload = create_payload("project")
    project_data = ProjectCreate(**payload)
    created_project = await ProjectCRUD.create(db=db_session, project=project_data)
    
    # Act - Call the API endpoint
    response = await async_client.get(f"/api/projects/{created_project.id}")
    
    # Assert - Verify the response
    assert response.status_code == 200
    
    # Validate the response schema
    validated = schema_validators["project"](response.json())
    assert validated.id == str(created_project.id)
    assert validated.name == created_project.name
    
    # Verify response content
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]