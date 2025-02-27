# Claude Assistant Guide for Noodle Projects

## Build & Test Commands
- Install: `pip install -r api/requirements.txt`
- Run server: `uvicorn app.main:app --reload`
- Test all: `pytest`
- Test with coverage: `pytest --cov=app --cov-report=term-missing --cov-report=html`
- Test specific file: `pytest api/tests/path/to/test_file.py -v`
- Test specific function: `pytest api/tests/path/to/test_file.py::test_function_name -v`

## Research Guidelines
- Use Perplexity proactively for:
  - Troubleshooting known issues and workarounds
  - Finding latest library/framework documentation
  - Accessing information updated since knowledge cutoff
  - Discovering technical solutions shared by the community

## Code Style Guidelines
- Follow PEP 8 guidelines with consistent indentation (4 spaces)
- Import order: stdlib → third-party → relative (alphabetical within groups)
- Type hints required for all functions/methods and return values
- Use snake_case for variables/functions, CamelCase for classes
- Async/await patterns throughout codebase
- Custom error handling with NoodleError exception class and ErrorType enum
- Comprehensive docstrings for all functions and classes
- SQL queries using SQLAlchemy ORM (not raw SQL)
- Tests required for all new features (minimum 80% coverage)
- API schemas defined with Pydantic v2
- Clear separation between models, schemas, and route handlers