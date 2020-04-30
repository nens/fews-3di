"""Script to start 3Di simulations from FEWS.
"""
# ^^^ This docstring is automatically used in the command line help text.
from fews_3di import simulation
from fews_3di import utils
from pathlib import Path

import argparse
import logging


# Exceptions we raise ourselves that are suitable for printing as error messages.
OWN_EXCEPTIONS = (
    simulation.AuthenticationError,
    simulation.InvalidDataError,
    simulation.MissingSavedStateError,
    simulation.NotFoundError,
    utils.MissingFileException,
    utils.MissingSettingException,
)


logger = logging.getLogger(__name__)


def get_parser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "-s",
        "--settings",
        dest="settings_file",
        default="run_info.xml",
        help="xml settings file",
    )
    parser.add_argument(
        "-m",
        "--allow-missing-saved-state",
        action="store_true",
        default=False,
        help="Allow a saved state to be initially missing",
    )
    return parser


def main():
    """Call main command with args from parser.

    This method is called when you run 'bin/run-fews-3di',
    this is configured in 'setup.py'. Adjust when needed. You can have multiple
    main scripts.

    """
    options = get_parser().parse_args()
    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    try:
        settings = utils.Settings(Path(options.settings_file))
        threedi_simulation = simulation.ThreediSimulation(
            settings, options.allow_missing_saved_state
        )
        threedi_simulation.login()
        threedi_simulation.run()
        return 0  # Success!
    except OWN_EXCEPTIONS as e:
        if options.verbose:
            logger.exception(e)
        else:
            logger.error("↓↓↓↓↓   Pass --verbose to get more information   ↓↓↓↓↓")
            logger.error(e)
        return 1  # Exit code signalling an error.
