"""Tests for utils.py"""
from fews_3di import utils
from pathlib import Path

import pytest


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"
WRONG_SETTINGS_FILE = TEST_DIR / "settings_without_username.xml"


def test_read_settings_smoke():
    utils.Settings(EXAMPLE_SETTINGS_FILE)


def test_read_settings_extracts_properties():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    assert settings.username == "pietje"


def test_read_settings_missing_username():
    with pytest.raises(utils.MissingSettingException):
        utils.Settings(WRONG_SETTINGS_FILE)


def test_read_settings_extracts_times():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    assert settings.start
    assert settings.end
    assert settings.start.day == 26


def test_read_settings_missing_date_item():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    with pytest.raises(utils.MissingSettingException):
        settings._read_datetime("middle")


def test_read_settings_duration():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    assert settings.duration == 352800
