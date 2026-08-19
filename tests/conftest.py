"""
Pytest configuration and session fixtures for Financial Fraud Detection test suite.
"""

import pytest
from scripts.cleanup_database import cleanup_test_records


@pytest.fixture(scope="session", autouse=True)
def clean_database_after_tests():
    """Runs test suite and cleanly purges any temporary test records on completion."""
    yield
    cleanup_test_records()
