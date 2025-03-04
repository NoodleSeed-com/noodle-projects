# Synchronous Conversion Plan

1. **Core Infrastructure Changes**:
   - Update database engine setup in config.py ✅
   - Remove AsyncSession imports and references ✅
   - Change DB dependency injection pattern ✅
   - Update FastAPI exception handlers ✅

2. **CRUD Operations**:
   - Convert ProjectCRUD methods ✅
   - Convert FileCRUD methods ✅ (partially complete)
   - Convert VersionCRUD methods ✅ (partially complete)
   - Remove await/async from all methods
   - Remove to_thread and any other async operations

3. **Route Handlers**:
   - Convert projects.py ✅
   - Convert versions.py
   - Update type hints from AsyncSession to Session
   - Remove async/await keywords

4. **Test Fixtures**:
   - Update db.py fixtures for synchronous operations
   - Convert test client setup from async to sync
   - Update all test files to use sync client

5. **Template and File Operations**:
   - Convert template.py to synchronous operations
   - Replace asyncio.to_thread calls with direct calls
   - Update file reading/writing to synchronous methods

6. **Services**:
   - Update openrouter.py service if async patterns used

This transformation will involve updating dozens of files, but we'll approach it methodically, starting with the core infrastructure and then moving out to the edges.
