"""Tests for utils.py

Note: the 'example_settings' pytest fixture is defined in conftest.py.

"""
from fews_3di import utils
from pathlib import Path

import pytest


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"
WRONG_SETTINGS_FILE = TEST_DIR / "settings_without_username.xml"
EXAMPLE_LATERAL_CSV = TEST_DIR / "example_lateral.csv"


def test_read_settings_smoke():
    utils.Settings(EXAMPLE_SETTINGS_FILE)


def test_read_settings_extracts_properties(example_settings):
    assert example_settings.username == "pietje"


def test_read_settings_missing_username():
    with pytest.raises(utils.MissingSettingException):
        utils.Settings(WRONG_SETTINGS_FILE)


def test_read_settings_extracts_times(example_settings):
    assert example_settings.start
    assert example_settings.end
    assert example_settings.start.day == 26


def test_read_settings_missing_date_item(example_settings):
    with pytest.raises(utils.MissingSettingException):
        example_settings._read_datetime("middle")


def test_read_settings_duration(example_settings):
    assert example_settings.duration == 352800


def test_read_settings_base_dir(example_settings):
    assert example_settings.base_dir == TEST_DIR


def test_lateral_timeseries_smoke(example_settings):
    utils.lateral_timeseries(EXAMPLE_LATERAL_CSV, example_settings)
