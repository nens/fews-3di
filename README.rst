fews-3di
==========================================

Program to start `3Di <https://3diwatermanagement.com/>`_ simulations from FEWS.


Installation and usage
----------------------

We can be installed using python 3.6+ with::

  $ pip install fews-3di

The script is called ``run-fews-3di``, you can pass ``--help`` to get usage
instructions and ``--verbose`` to get more verbose output in case of
problems.

``run-fews-3di`` looks for a ``run_info.xml`` in the current directory by
default, but you can pass a different file in a different location with
``--settings``.

Several input files are needed, they should be in the ``input`` directory
**relative** to the ``run_info.xml``, like ``input/evaporation.nc``.
Output is stored in the ``output`` directory relative to the ``run_info.xml``.


Development instructions (only for the programmers, not for regular use)
------------------------------------------------------------------------

We use python's build-in "virtualenv" to get a nice isolated directory. You
only need to run this once::

  $ python3 -m venv .

A virtualenv puts its commands in the ``bin`` directory. So ``bin/pip``,
``bin/pytest``, etc. Set up the dependencies like this::

  $ bin/pip install -r requirements.txt

There will be a script you can run like this::

  $ bin/run-fews-3di

It runs the `main()` function in `fews-3di/scripts.py`,
adjust that if necessary. The script is configured in `setup.py` (see
`entry_points`).

In order to get nicely formatted python files without having to spend manual
work on it, run the following command periodically::

  $ bin/black fews_3di

Run the tests regularly. This also checks with pyflakes, black and it reports
coverage. Pure luxury::

  $ bin/pytest

The tests are also run automatically `on "github actions"
<https://githug.com/nens/fews-3di/actions>`_ for
"master" and for pull requests. So don't just make a branch, but turn it into
a pull request right away:

- Prepend the title with "[WIP]", work in progress. That way you make clear it
  isn't ready yet to be merged.

- **Important**: it is easy to give feedback on pull requests. Little comments
  on the individual lines, for instance. So use it to get early feedback, if
  you think that's useful.

- On your pull request page, you also automatically get the feedback from the
  automated tests.

There's also
`coverage reporting <https://coveralls.io/github/nens/fews-3di>`_
on coveralls.io.

If you need a new dependency (like ``requests``), add it in ``setup.py`` in
``install_requires``. Local development tools, like "black", can be added to the
``requirements.txt`` directoy. In both cases, run install again to actuall
install your dependency::

  $ bin/pip install -r requirements.txt
