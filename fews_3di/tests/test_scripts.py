"""Tests for script.py"""
from fews_3di import scripts

import mock


def test_get_parser():
    parser = scripts.get_parser()
    # As a test, we just check one option. That's enough.
    with mock.patch("sys.argv", ["program"]):
        options = parser.parse_args()
        assert not options.verbose
