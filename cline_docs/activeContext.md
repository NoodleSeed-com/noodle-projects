# Active Context

## Current Focus

- Validating and documenting version number semantics in the FastAPI application.
- Ensuring proper constraints and validation at both database and API levels.
- Maintaining comprehensive documentation of system patterns.

## Recent Changes

- Added CHECK constraint to enforce non-negative version numbers.
- Added UNIQUE constraint to prevent duplicate version numbers within projects.
- Added comprehensive tests for version number semantics:
  - Version number uniqueness
  - Version number validation
  - Version ordering
  - Parent-child relationships
  - Version persistence after project soft deletion
- Updated systemPatterns.md with detailed version number semantics documentation.

## Next Steps

- Consider implementing an endpoint for creating new versions.
- Consider adding validation for parent-child relationship integrity.
- Consider adding version number sequence validation if needed.

## Active Decisions and Considerations

- Version numbers must be unique within a project but can be reused across projects.
- Version numbers persist when a project is soft-deleted (preserving history).
- Version numbers do not need to be sequential (gaps allowed).
- Parent-child relationships are supported through parent_version_id.
- All version number validation tests are now passing.

## Current CLI Operations and Workflows

- Running tests: `cd api && python -m pytest tests/test_projects.py -v`
- All tests passing, including new version number semantics tests.
