# Project Brief: Projects API Microservice

## Overview
A FastAPI-based microservice for managing projects and their versions, with version control and file management through a RESTful API.

## Core Requirements

### Project Management
- Create, read, update, and soft-delete projects
- Track project metadata and status
- Maintain latest version number

### Version Control
- Automatic version numbering
- Parent-child version relationships
- No explicit version creation endpoint

### File Management
- Store files associated with versions
- Enforce unique file paths within versions
- No direct file manipulation endpoints

## Technical Specifications
- RESTful API with proper error handling
- PostgreSQL with UUID keys, timestamps, soft deletion
- FastAPI, SQLAlchemy ORM, Pydantic models
- Environment-based configuration

## Future Scope
- Batch operations
- Advanced version querying
- Search capabilities
- Additional metadata fields
- Performance monitoring
