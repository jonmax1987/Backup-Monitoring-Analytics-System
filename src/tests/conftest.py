"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    # Assuming tests are in src/tests/
    return Path(__file__).parent.parent.parent


@pytest.fixture
def config_dir(project_root):
    """Return the config directory."""
    return project_root / "config"
