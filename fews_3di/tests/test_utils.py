"""Tests for utils.py

Note: the 'example_settings' pytest fixture is defined in conftest.py.

"""
from fews_3di import utils
from pathlib import Path

import datetime
import pytest


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"
WRONG_SETTINGS_FILE = TEST_DIR / "settings_without_username.xml"
EXAMPLE_LATERAL_CSV = TEST_DIR / "example_lateral.csv"
EXAMPLE_PRECIPITATION_FILE = TEST_DIR / "precipitation.nc"
EXAMPLE_EVAPORATION_FILE = TEST_DIR / "evaporation.nc"


def test_read_settings_smoke():
    utils.Settings(EXAMPLE_SETTINGS_FILE)


# Note: example_settings is an automatic fixture, see conftest.py
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
    assert (example_settings.base_dir / "example_settings.xml").exists()
    assert (example_settings.base_dir / "input").exists()


def test_read_settings_save_state(example_settings):
    assert example_settings.save_state is True


def test_lateral_timeseries_smoke(example_settings):
    utils.lateral_timeseries(EXAMPLE_LATERAL_CSV, example_settings)


def test_lateral_timeseries_file_missing(example_settings):
    with pytest.raises(utils.MissingFileException):
        utils.lateral_timeseries(Path("boodschappenlijst.csv"), example_settings)


def test_lateral_timeseries_omit_early_timestamps(example_settings):
    # The example laterals csv has some 2020-01-21 timestamps. Check that
    # they're omitted when we adjust the start date.
    example_settings.start = datetime.datetime(year=2020, month=1, day=22)
    utils.lateral_timeseries(EXAMPLE_LATERAL_CSV, example_settings)
    # Just a smoke test atm for code coverage.


def test_timestamps_from_netcdf():
    timestamps = utils.timestamps_from_netcdf(EXAMPLE_PRECIPITATION_FILE)
    assert len(timestamps)
    assert timestamps[0].day == 21
    assert timestamps[0].hour == 12
    assert timestamps[-1].day == 30
    assert timestamps[-1].hour == 12


def test_write_netcdf_with_time_indexes(example_settings):
    result = utils.write_netcdf_with_time_indexes(
        EXAMPLE_PRECIPITATION_FILE, example_settings
    )
    assert result.exists()
    assert result.name == "precipitation.nc"


def test_write_netcdf_with_time_indexes_missing_file(example_settings):
    with pytest.raises(utils.MissingFileException):
        utils.write_netcdf_with_time_indexes(Path("pietje.nc"), example_settings)
