from fews_3di import simulation
from openapi_client.exceptions import ApiException

import mock
import pytest


# Note: example_settings is an automatic fixture, see conftest.py
def test_init(example_settings):
    simulation.ThreediSimulation(example_settings)


def test_login_fails(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    # The example settings of course give an authentication error.
    with pytest.raises(simulation.AuthenticationError):
        threedi_simulation.login()


def test_login_fails_unknown(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    with mock.patch("openapi_client.AuthApi.auth_token_create") as mocked:
        mocked.side_effect = ApiException(status=500)
        with pytest.raises(ApiException):
            threedi_simulation.login()


def test_login_succeeds(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    with mock.patch("openapi_client.AuthApi.auth_token_create") as mocked:
        mock_response = mock.Mock()
        mock_response.access = "my tokens"
        mocked.side_effect = [mock_response]
        threedi_simulation.login()
        assert threedi_simulation.configuration.api_key["Authorization"] == "my tokens"


def test_run_mock_mock_mock(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    threedi_simulation._find_model = mock.MagicMock(return_value=42)
    threedi_simulation._create_simulation = mock.MagicMock(
        return_value=(43, "https://example.org/model/43/")
    )
    threedi_simulation._add_laterals = mock.MagicMock()
    threedi_simulation._add_initial_state = mock.MagicMock()
    threedi_simulation._prepare_initial_state = mock.MagicMock(return_value=21)
    threedi_simulation._add_rain = mock.MagicMock()
    threedi_simulation._add_evaporation = mock.MagicMock()
    threedi_simulation._run_simulation = mock.MagicMock()
    threedi_simulation._download_results = mock.MagicMock()
    threedi_simulation._process_basic_lizard_results = mock.MagicMock()
    # ._write_saved_state_id() doesn't need mocking.
    threedi_simulation._process_results = mock.MagicMock()

    threedi_simulation.run()


def test_find_model(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    threedi_simulation.threedimodels_api = mock.Mock()
    # Pfffff, it is a bit hard to mock all this stuff...
    mock_result = mock.Mock()
    mock_model = mock.Mock()
    mock_model.id = 42
    mock_result.results = [mock_model]
    threedi_simulation.threedimodels_api.threedimodels_list = mock.MagicMock(
        return_value=mock_result
    )
    assert threedi_simulation._find_model() == 42


def test_find_model_not_found(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    threedi_simulation.threedimodels_api = mock.Mock()
    # Pfffff, it is a bit hard to mock all this stuff...
    mock_result = mock.Mock()
    mock_result.results = []
    threedi_simulation.threedimodels_api.threedimodels_list = mock.MagicMock(
        return_value=mock_result
    )
    with pytest.raises(simulation.NotFoundError):
        threedi_simulation._find_model()


def test_add_laterals(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    threedi_simulation.simulations_api = mock.Mock()
    threedi_simulation.simulation_id = 1
    laterals = {"name 1": [mock.Mock()]}
    mock_lateral = mock.Mock()
    threedi_simulation.simulations_api.simulations_events_lateral_timeseries_create = (
        mock.MagicMock(return_value=mock_lateral)
    )
    mock_lateral2 = mock.Mock()
    mock_lateral2.state = "valid"
    threedi_simulation.simulations_api.simulations_events_lateral_timeseries_read = (
        mock.MagicMock(return_value=mock_lateral2)
    )

    threedi_simulation._add_laterals(laterals)  # Should just return None
