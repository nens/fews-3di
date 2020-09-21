Changelog of fews-3di
===================================================


1.5 (2020-09-21)
----------------

- Added more resilience to local network errors. The loop that waits for
  results to be ready checks the state every 30 seconds and is thus the most
  vulnerable to wifi issues, a flaky VPN and local network hickups. We now
  detect such a ``socket.gaierror`` there and simply try again in 30 seconds.


1.4 (2020-07-21)
----------------

- A minor bugfix in the result files which are downloaded after the simulation


1.3 (2020-07-16)
----------------

- A minor bugfix in the location where the script searches for the saved-state
  file


1.2 (2020-07-09)
----------------

- The code has been set-up to look for specific filenames in predefined
  folders.

- All inputs (rain, evaporation etc.) have now become optional, if one is
  absent a logging message is returned but the code will run. This allows for
  flexibility in the usage of the code with different kinds of input.

- Two new optional parameters have been added: lizard_results_scenario_uuid and
  lizard_results_scenario_name. If a Lizard results   scenario name is provided,
  results will be processed in Lizard. If it is not provided, the simulation
  runs as usual without processing.


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
