from fews_3di import simulation

import pytest


def test_smoke(example_settings):
    simulation.ThreediSimulation(example_settings)


def test_auth_fails(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    # The example settings of course give an authentication error.
    with pytest.raises(simulation.AuthenticationError):
        threedi_simulation.login()
