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
``--settings``::

  $ run-fews-3di
  $ run-fews-3di --help
  $ run-fews-3di --settings /some/directory/run_info.xml

Several input files are needed, they should be in the ``input`` directory
**relative** to the ``run_info.xml``, like ``input/evaporation.nc``.
Output is stored in the ``output`` directory relative to the ``run_info.xml``.



Development
-----------

Development happens on github. See ``DEVELOPMENT.rst`` for more information.
