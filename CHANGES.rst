Changelog of fews-3di
===================================================


2.0 (2022-06-21)
----------------

- Requiring threedi-api-client 4.0.1 or higher. This has several import and
  functionality changes, which we'll have to use (and compensate for). Some
  items to watch out for:

  - The api host setting should not include the api version number.

  - Preferrably, don't add a trailing slash to the api host url.

- ``.login()`` no longer needs to be called. threedi-api-client handles it
  automatically. If you call it, you get a deprecation warning.

- ``--allow-missing-saved-state`` also works if there are no states found.


1.15 (2022-06-10)
-----------------

- Added optional api_host parameter to the settings file.


1.14 (2022-02-08)
-----------------

- Added missing requests dependency to package setup.


1.13 (2021-09-01)
-----------------

- Added possibility to write state at specific time intervall.


1.12 (2021-04-28)
-----------------

- Fixes for 1.11, initial waterlevel should work now.


1.11 (2021-04-28)
-----------------

- Added possibility to add initial waterlevel raster.


1.10 (2021-02-09)
-----------------

- Added the functionality to provide a cold state file.
  Place next to original state file with the name:
  3di-cold-state-id.txt.


1.9 (2021-01-27)
----------------

- Added new rainfall modules, constant, csv and radar rain.

- Processing results into fews is now optional.


1.7 (2020-11-13)
----------------

- Checks for crashed status and queue's model.


1.6 (2020-10-19)
----------------

- Using a "streaming" download of large files to prevent partial downloads.


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
