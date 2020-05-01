from fews_3di import simulation
from openapi_client.exceptions import ApiException

import mock
import pytest


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
    # ._write_saved_state_id() doesn't need mocking.
    threedi_simulation._process_results = mock.MagicMock()

    threedi_simulation.run()
