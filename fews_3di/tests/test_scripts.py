"""Tests for script.py"""
from fews_3di import scripts

import mock
import pytest


def test_get_parser():
    parser = scripts.get_parser()
    # As a test, we just check one option. That's enough.
    with mock.patch("sys.argv", ["program"]):
        options = parser.parse_args()
        assert not options.verbose


def test_main_help():
    with mock.patch("sys.argv", ["program", "--help"]):
        with pytest.raises(SystemExit):
            scripts.main()


def test_main_verbose():
    # Smoke test.
    with mock.patch("sys.argv", ["program", "--verbose"]):
        scripts.main()


def test_main_error():
    with mock.patch("sys.argv", ["program", "--settings", "missing.txt"]):
        assert scripts.main() == 1  # Exit error code.


# Note: example_settings is an automatic fixture, see conftest.py
def test_main_login_error(example_settings):
    with mock.patch(
        "sys.argv", ["program", "--settings", str(example_settings.settings_file)]
    ):

        assert scripts.main() == 1  # exit code 1: expected login error.


def test_main_login_error_verbose(example_settings):
    with mock.patch(
        "sys.argv",
        ["program", "--verbose", "--settings", str(example_settings.settings_file)],
    ):

        assert scripts.main() == 1  # exit code 1: expected login error.


def test_main_dummy_run(example_settings):
    with mock.patch(
        "sys.argv", ["program", "--settings", str(example_settings.settings_file)]
    ):
        with mock.patch("fews_3di.scripts.simulation.ThreediSimulation"):
            assert scripts.main() == 0  # Success
