"""Pytest fixtures for the tests."""
from fews_3di import utils
from pathlib import Path

import pytest


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"


@pytest.fixture
def example_settings():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    return settings
