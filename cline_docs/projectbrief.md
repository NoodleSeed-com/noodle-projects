# Project Brief: Projects API Microservice

## Overview
A FastAPI-based microservice for managing projects and their versions, with a focus on version control and file management through a RESTful API interface.

## Core Requirements

### Project Management
- [x] Create, read, update, and soft-delete projects
- [x] Track project metadata (name, description)
- [x] Maintain project status (active/inactive)
- [x] Track latest version number

### Version Control
- [x] Automatic version numbering
- [x] Parent-child version relationships
- [x] Version naming support
- [x] No explicit version creation endpoint

### File Management
- [x] Store files associated with versions
- [x] Enforce unique file paths within versions
- [x] No direct file manipulation endpoints
- [x] Maintain file content and metadata

## Technical Specifications

### API Design
- [x] RESTful endpoints
- [x] Proper error handling
- [x] Input validation
- [x] Pagination support

### Database Schema
- [x] UUID primary keys
- [x] Timestamp tracking
- [x] Soft deletion
- [x] Foreign key constraints
- [x] Optimized indexes
- [x] Unique constraints

### Implementation
- [x] FastAPI framework
- [x] SQLAlchemy ORM
- [x] Pydantic models
- [x] Environment-based configuration

## Documentation
- [x] API documentation (OpenAPI/Swagger)
- [x] Setup instructions
- [x] Database schema documentation
- [x] Code documentation
- [x] Memory Bank documentation

## Future Scope
- [ ] Batch operations
- [ ] Advanced version querying
- [ ] Search capabilities
- [ ] Additional metadata fields
- [ ] Performance monitoring
