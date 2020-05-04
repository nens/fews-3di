Changelog of fews-3di
===================================================


1.1 (2020-05-04)
----------------

- When an existing saved state isn't found, it can be because it is the first
  time the script is run. Or the previous saved data has expired. The error
  message now points at the ``--allow-missing-saved-state`` possibility. This
  can be used to allow the missing of the saved state: a new one will be
  created.

- Fixed bug: two lines were accidentally swapped, leading to an early crash.


1.0 (2020-05-04)
----------------

- Code cleanup + more coverage.

- Improved the documentation, including a separate ``DEVELOPMENT.rst`` to keep
  those details out of the generic readme.


0.4 (2020-04-30)
----------------

- Reading and storing saved states added.


0.3 (2020-04-23)
----------------

- Release mechanism fix.


0.2 (2020-04-23)
----------------

- Added lateral upload.

- Added rain upload.

- Added evaporation upload.

- Simulation is actually being run now.

- Added processing of the results.

- Added usage instructions.


0.1 (2020-04-09)
----------------

- Started copying code from the old project.

- Got 3Di api connection to work, including creating an (empty) simulation.

- Initial project structure created with cookiecutter and
  https://github.com/nens/cookiecutter-python-template
