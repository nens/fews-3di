"""Tests for utils.py"""
from fews_3di import utils
from pathlib import Path


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"


def test_smoke():
    assert isinstance(utils.read_settings(EXAMPLE_SETTINGS_FILE), dict)
