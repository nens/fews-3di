Development instructions
========================


Development installation
------------------------

To install::

  $ make install

If you want to use a specific version of python, you can first run something
like this::

  $ python3.9 -m venv .

There will be a script you can run like this::

  $ bin/run-fews-3di

It runs the ``main()`` function in ``fews-3di/scripts.py``, adjust that if
necessary. The script is configured in ``setup.py`` (see ``entry_points``).

If you need a new dependency (like ``requests``), add it in ``setup.py`` in
``install_requires``. Local development tools, like "black", can be added to
the ``requirements.txt`` file. In both cases, run ``make install`` again.


Code structure
--------------

- ``fews_3di/scripts.py``: the ``run-fews-3di`` code. Should only handle the
  commandline stuff and logging setup.

- ``fews_3di/simulation.py``: the main ``ThreediSimulation`` class. The
  various steps like "add rain" and "start simulation" are separate methods on
  that class: this way you can keep the overview of what's happening. It is a
  class to make it easier to share common data like "simulation id".

- ``fews_3di/utils.py``: reading the settings plus some helper functions like
  ``timestamps_from_netcdf()``.

- ``fews_3di/tests/*``: the tests, including sample data.


Error handling and logging
--------------------------

Try/excepts are only used when strictly necessary. Unexpected errors will
simply be shown as a traceback.

Some errors are expected, like a missing setting or a missing netcdf file. For
these, there's an explicit error class like ``MissingSettingException``. These
are caught in ``scripts.py`` and shown as a neat error message. With
``--verbose``, you also get the traceback.

Debug logging is used to make it easy to figure out what the program is doing
in case of a problem or an unexpected result.

Info level logging is for feedback to the user. Don't log too much on this
level.

Warning/error are the usual. An error when something is wrong and we're
stopping the script. A warning for when something *seems* wrong, but when
we'll continue execution anyway.



Neatness and tests
------------------

In order to get nicely formatted python files without having to spend manual
work on it, run the following command periodically::

  $ make beautiful

If you don't have "make" installed, look in the Makefile for the commands it
runs (black, flake8, isort).

Run the tests regularly, this includes pyflakes and black checks::

  $ make test

Running pytest by itself is also possible, for instance if you want to pass
specific options::

  $ bin/pytest --disable-warnings

The tests are also run automatically `on "github actions"
<https://github.com/nens/fews-3di/actions>`_ for
"master" and for pull requests. So don't just make a branch, but turn it into
a pull request right away:

- **Important**: it is easy to give feedback on pull requests. Little comments
  on the individual lines, for instance. So use it to get early feedback, if
  you think that's useful.

- On your pull request page, you also automatically get the feedback from the
  automated tests.

There's also
`coverage reporting <https://coveralls.io/github/nens/fews-3di>`_
on coveralls.io.

As an **experiment**, python type hints are sprinkled throughout the
code. When running the tests, errors are often found. The reason for the
experiment was some confusion in the original version of fews-3di:

- A string "True" from the settings instead of a proper boolean True/False
  value.

- Timestamps that were sometimes datetime objects and sometimes iso-formatted
  datetime strings.

With type hints, it is perfectly clear what something is supposed to be.


Releases
--------

Before releasing, make sure the changelog is up to date, otherwise
zest.releaser complains :-) Then run fullrelease::

  $ bin/fullrelease

Github detects the new tag and automatically uploads a new release to
https://pypi.org/project/fews-3di/
