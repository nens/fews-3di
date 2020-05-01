"""Pytest fixtures for the tests."""
from fews_3di import utils
from pathlib import Path

import pytest
import shutil


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILENAME = "example_settings.xml"


@pytest.fixture
def example_settings(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    shutil.copy(
        TEST_DIR / EXAMPLE_SETTINGS_FILENAME, tmp_path / EXAMPLE_SETTINGS_FILENAME
    )
    shutil.copy(TEST_DIR / "example_lateral.csv", input_dir / "lateral.csv")
    shutil.copy(TEST_DIR / "precipitation.nc", input_dir / "precipitation.nc")
    shutil.copy(TEST_DIR / "evaporation.nc", input_dir / "evaporation.nc")

    settings = utils.Settings(tmp_path / EXAMPLE_SETTINGS_FILENAME)
    return settings
