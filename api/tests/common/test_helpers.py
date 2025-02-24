"""
Helper functions and utilities for concurrent testing.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, TypeVar, Dict, Any
from fastapi.testclient import TestClient

T = TypeVar('T')

def run_concurrent_requests(
    client: TestClient,
    request_fn: Callable[[int], T],
    count: int,
    max_workers: int = None
) -> List[T]:
    """Run multiple requests concurrently using ThreadPoolExecutor.
    
    Args:
        client: FastAPI TestClient instance
        request_fn: Function that takes an index and returns a response
        count: Number of concurrent requests to make
        max_workers: Maximum number of worker threads (defaults to count)
    
    Returns:
        List of responses in order of completion
    """
    max_workers = max_workers or count
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(request_fn, i)
            for i in range(count)
        ]
        return [f.result() for f in as_completed(futures)]

def assert_unique_responses(
    responses: List[Dict[str, Any]], 
    key: str,
    success_code: int = 200
) -> None:
    """Assert that successful responses have unique values for a given key.
    
    Args:
        responses: List of response dictionaries
        key: Key to check for uniqueness
        success_code: Expected success status code
    """
    # Get values from successful responses
    values = [
        r.json()[key] 
        for r in responses 
        if r.status_code == success_code
    ]
    # Assert values are unique
    assert len(values) == len(set(values)), f"Duplicate {key} values found: {values}"

def assert_response_mix(
    responses: List[Dict[str, Any]],
    expected_codes: List[int]
) -> None:
    """Assert that responses contain expected mix of status codes.
    
    Args:
        responses: List of response dictionaries
        expected_codes: List of expected status codes
    """
    actual_codes = [r.status_code for r in responses]
    for code in expected_codes:
        assert code in actual_codes, f"Expected status code {code} not found in responses"

def assert_database_constraints(
    responses: List[Dict[str, Any]],
    client: TestClient,
    project_id: str,
    version_key: str = "version_number"
) -> None:
    """Assert that database constraints are maintained after concurrent operations.
    
    Args:
        responses: List of response dictionaries
        client: FastAPI TestClient instance
        project_id: Project ID to check
        version_key: Key for version number in response
    """
    # Get all versions from database
    versions_response = client.get(f"/api/projects/{project_id}/versions")
    assert versions_response.status_code == 200
    db_versions = versions_response.json()
    
    # Get successful response version numbers
    response_versions = [
        r.json()[version_key]
        for r in responses
        if r.status_code == 200
    ]
    
    # Verify all successful response versions exist in database
    db_version_numbers = [v["version_number"] for v in db_versions]
    for version in response_versions:
        assert version in db_version_numbers, f"Version {version} not found in database"
    
    # Verify no duplicate version numbers in database
    assert len(db_version_numbers) == len(set(db_version_numbers)), \
        "Duplicate version numbers found in database"

def assert_file_constraints(
    responses: List[Dict[str, Any]],
    client: TestClient,
    project_id: str,
    version_number: int,
    file_path: str
) -> None:
    """Assert that file constraints are maintained after concurrent operations.
    
    Args:
        responses: List of response dictionaries
        client: FastAPI TestClient instance
        project_id: Project ID to check
        version_number: Version number to check
        file_path: File path to verify
    """
    # Get version details from database
    version_response = client.get(
        f"/api/projects/{project_id}/versions/{version_number}"
    )
    assert version_response.status_code == 200
    version_data = version_response.json()
    
    # Check for file path uniqueness
    matching_files = [
        f for f in version_data["files"]
        if f["path"] == file_path
    ]
    assert len(matching_files) == 1, \
        f"Expected exactly one file with path {file_path}, found {len(matching_files)}"
