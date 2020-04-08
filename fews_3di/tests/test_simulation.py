from fews_3di import simulation
from fews_3di import utils
from pathlib import Path

import pytest


TEST_DIR = Path(__file__).parent
EXAMPLE_SETTINGS_FILE = TEST_DIR / "example_settings.xml"


@pytest.fixture
def example_settings():
    settings = utils.Settings(EXAMPLE_SETTINGS_FILE)
    return settings


def test_smoke(example_settings):
    simulation.ThreediSimulation(example_settings)


def test_auth_fails(example_settings):
    threedi_simulation = simulation.ThreediSimulation(example_settings)
    # The example settings of course give an authentication error.
    with pytest.raises(simulation.AuthenticationError):
        threedi_simulation.login()
