# Product Context

## Purpose
The Projects API is a microservice for managing projects and their versions through a RESTful interface, focusing on version management without direct file manipulation.

## Core Functionality

### Project Management
- Create and manage projects with metadata
- Track project status through active flag
- Support soft deletion to preserve history

### Version Control
- Automatic version numbering within projects
- Track parent-child relationships between versions
- Version naming for human-readable identification

### File Storage
- Internal file storage associated with versions
- Enforce unique file paths within version scope
- Maintain file content and metadata

## Design Philosophy
- API-first with clean RESTful interface
- Data integrity through constraints and validation
- Performance through optimized database design
- Async operations for scalability

## Integration Points
- PostgreSQL via Supabase
- RESTful API with JSON format
- Pagination support

## Security Considerations
- No direct file access through API
- Row Level Security enabled
- Proper indexing and constraints

## Future Considerations
- Batch operations
- Advanced version querying
- Enhanced search capabilities
- Additional metadata fields
