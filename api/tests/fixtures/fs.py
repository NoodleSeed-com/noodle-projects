"""
File system fixtures for tests.

This module provides fixtures for managing temporary files and directories.
"""
import os
import shutil
import tempfile
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for tests.
    
    This fixture creates a temporary directory that is automatically deleted
    after the test completes, ensuring clean test isolation.
    
    Returns:
        Path: Path to the temporary directory
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    
    # Clean up after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file():
    """
    Create a temporary file for tests.
    
    This fixture creates a temporary file that is automatically deleted
    after the test completes.
    
    Returns:
        callable: A function that creates a temporary file with the given content
    """
    temp_files = []
    
    def _create_temp_file(content="", suffix=".txt"):
        """
        Create a temporary file with the given content.
        
        Args:
            content: The content to write to the file
            suffix: The file extension
            
        Returns:
            Path: Path to the temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        temp_files.append(path)
        
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        return Path(path)
    
    yield _create_temp_file
    
    # Clean up all created files
    for file_path in temp_files:
        try:
            os.unlink(file_path)
        except (OSError, PermissionError):
            pass


@pytest.fixture
def temp_template_dir():
    """
    Create a temporary template directory for tests.
    
    This fixture creates a temporary directory for templates and configures
    the application to use it, ensuring template operations don't affect
    the real template directory.
    
    Returns:
        Path: Path to the temporary template directory
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_version_dir = os.path.join(temp_dir, 'version-0')
    os.makedirs(temp_version_dir, exist_ok=True)
    
    # Store original setting
    original_template_path = settings.TEMPLATE_PATH
    
    # Update setting to use temporary directory
    settings.TEMPLATE_PATH = temp_dir
    
    # Create sample template files
    template_files = {
        "package.json": '{"name":"test-project","version":"1.0.0"}',
        "tsconfig.json": '{"compilerOptions":{"target":"es5"}}',
        "public/index.html": "<!DOCTYPE html><html><head></head><body></body></html>",
        "src/App.tsx": "export const App = () => <div>App</div>;",
        "src/index.tsx": "import React from 'react';",
        "src/components/HelloWorld.tsx": "export const HelloWorld = () => <div>Hello World</div>;"
    }
    
    # Create the template files in the temporary directory
    for file_path, content in template_files.items():
        full_path = os.path.join(temp_version_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    yield Path(temp_dir)
    
    # Restore original setting and clean up
    settings.TEMPLATE_PATH = original_template_path
    shutil.rmtree(temp_dir, ignore_errors=True)