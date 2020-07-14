"""Pytest fixtures for the tests.

If you see a test like ``def test_something(example_settings)``, the
example_settings is a "fixture" that the function with the same name (see
below) returns. In this case a settings object in a temp directory with the
necessary sample data.

"""
from fews_3di import utils
from pathlib import Path

import pytest
import shutil


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILENAME = "example_settings.xml"


@pytest.fixture
def example_settings(tmp_path):
    input_dir = tmp_path / "input"
    model_dir = tmp_path / "model"
    output_dir = tmp_path / "output"
    states_dir = tmp_path / "states"
    input_dir.mkdir()
    model_dir.mkdir()
    output_dir.mkdir()
    states_dir.mkdir()

    shutil.copy(
        TEST_DIR / EXAMPLE_SETTINGS_FILENAME, tmp_path / EXAMPLE_SETTINGS_FILENAME
    )
    shutil.copy(TEST_DIR / "example_lateral.csv", input_dir / "lateral.csv")
    shutil.copy(TEST_DIR / "precipitation.nc", input_dir / "precipitation.nc")
    shutil.copy(TEST_DIR / "evaporation.nc", input_dir / "evaporation.nc")
    shutil.copy(TEST_DIR / "ow.nc", input_dir / "ow.nc")
    shutil.copy(TEST_DIR / "gridadmin.h5", model_dir / "gridadmin.h5")

    settings = utils.Settings(tmp_path / EXAMPLE_SETTINGS_FILENAME)
    return settings
