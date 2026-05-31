"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_data():
    """Return sample data for testing."""
    return {
        "voltage": [12.0, 12.0, 12.0],
        "current": [1.0, 1.5, 2.0],
        "time": [0.0, 0.1, 0.2],
    }
