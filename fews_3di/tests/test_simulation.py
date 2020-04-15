from fews_3di import simulation
from openapi_client.exceptions import ApiException

import mock
import pytest


def test_smoke(example_settings):
    simulation.ThreediSimulation(example_settings)


def test_auth_fails(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    # The example settings of course give an authentication error.
    with pytest.raises(simulation.AuthenticationError):
        threedi_simulation.login()


def test_auth_fails_unknown(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    with mock.patch("openapi_client.AuthApi.auth_token_create") as mocked:
        mocked.side_effect = ApiException(status=500)
        with pytest.raises(ApiException):
            threedi_simulation.login()


def test_auth_succeeds(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    with mock.patch("openapi_client.AuthApi.auth_token_create") as mocked:
        mock_response = mock.Mock()
        mock_response.access = "my tokens"
        mocked.side_effect = [mock_response]
        threedi_simulation.login()
        assert threedi_simulation.configuration.api_key["Authorization"] == "my tokens"
