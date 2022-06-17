from fews_3di import simulation

import mock
import pytest


# Note: example_settings is an automatic fixture, see conftest.py
def test_init(example_settings):
    simulation.ThreediSimulation(example_settings)


def test_login_deprecated(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    with pytest.deprecated_call():
        # .deprecated_call() fails if there isn't a DeprecationWarning.
        threedi_simulation.login()


def test_run_mock_mock_mock(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    threedi_simulation._find_model = mock.MagicMock(return_value=42)
    threedi_simulation._create_simulation = mock.MagicMock(
        return_value=(43, "https://example.org/model/43/")
    )
    threedi_simulation._add_laterals = mock.MagicMock()
    threedi_simulation._add_last_available_state = mock.MagicMock()
    threedi_simulation._add_initial_state = mock.MagicMock()
    threedi_simulation._prepare_initial_state = mock.MagicMock(return_value=21)
    threedi_simulation._add_constant_rain = mock.MagicMock()
    threedi_simulation._add_radar_rain = mock.MagicMock()
    threedi_simulation._add_netcdf_rain = mock.MagicMock()
    threedi_simulation._add_csv_rain = mock.MagicMock()
    threedi_simulation._add_evaporation = mock.MagicMock()
    threedi_simulation._run_simulation = mock.MagicMock()
    threedi_simulation._download_results = mock.MagicMock()
    threedi_simulation._process_basic_lizard_results = mock.MagicMock()
    threedi_simulation._add_initial_waterlevel_raster = mock.MagicMock()
    # ._write_saved_state_id() doesn't need mocking.
    threedi_simulation._process_results = mock.MagicMock()

    threedi_simulation.run()
