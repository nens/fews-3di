"""Script to start 3Di simulations from FEWS.
"""
# ^^^ This docstring is automatically used in the command line help text.
from fews_3di import utils
from fews_3di.simulation import run_simulation
from pathlib import Path

import argparse
import logging


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
        run_simulation(settings)
    except Exception:  # TODO: just print the error for known exceptions.
        logger.exception("An exception has occurred.")
        return 1
