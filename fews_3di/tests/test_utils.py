"""Tests for utils.py"""
from fews_3di import utils
from pathlib import Path


# import pytest

TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"


def test_read_settings_smoke():
    assert isinstance(utils.read_settings(EXAMPLE_SETTINGS_FILE), dict)


def test_read_settings_extracts_properties():
    settings = utils.read_settings(EXAMPLE_SETTINGS_FILE)
    assert settings["username"] == "pietje"
