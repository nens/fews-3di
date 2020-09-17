"""
Notes
=====

Importing openapi_client: that way you can only have one generated
openapi_client. So not lizard and 3di next to each other?

threedi_api_client looks like a bit of a mess. ThreediApiClient doesn't have
an init, but a __new__. And it doesn't return a ThreediApiCLient, but
something else. ThreediApiClient doesn't even inherit from that other
thingy... That's not something that mypy with its proper type hints is going
to like very much...

APIConfiguration is at least a wrapper around Configuration. But somehow it
generates an api_client inside _get_api_tokens(), which it passes part of its
own configuration.... That looks terribly unclean.

Probably too much is happening. Configuration belongs in the apps that use
it. Some helper is OK, but it took me half an hour to figure out what was
happening where...

"""

from fews_3di import utils
from pathlib import Path
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from typing import List
from typing import Tuple

import datetime
import logging
import netCDF4
import openapi_client
import pandas as pd
import requests
import socket
import time

API_HOST = "https://api.3di.live/v3.0"
SAVED_STATE_ID_FILENAME = "3di-saved-state-id.txt"
SIMULATION_STATUS_CHECK_INTERVAL = 30
USER_AGENT = "fews-3di (https://github.com/nens/fews-3di/)"

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidDataError(Exception):
    pass


class MissingSavedStateError(Exception):
    pass


class ThreediSimulation:
    """Wrapper for a set of 3di API calls.

    To make testing easier, we don't call everything from the
    ``__init__()``. It is mandatory to call ``login()`` and ``run()`` after
    ``__init__()``.

    login(), as expected, logs you in to the 3Di api.

    run() runs all the required simulation steps.

    All the other methods are private methods (prefixed with an underscore) so
    that it is clear that they're "just" helper methods. By reading run(), it
    ought to be clear to see what's happening.

    """

    allow_missing_saved_state: bool
    api_client: openapi_client.ApiClient
    configuration: openapi_client.Configuration
    output_dir: Path
    saved_state_id: int
    settings: utils.Settings
    simulation_id: int
    simulation_url: str
    simulations_api: openapi_client.SimulationsApi
    threedimodels_api: openapi_client.ThreedimodelsApi

    def __init__(
        self, settings: utils.Settings, allow_missing_saved_state: bool = False
    ):
        """Set up a 3di API connection."""
        self.settings = settings
        self.allow_missing_saved_state = allow_missing_saved_state
        self.configuration = openapi_client.Configuration(host=API_HOST)
        self.api_client = openapi_client.ApiClient(self.configuration)
        self.api_client.user_agent = USER_AGENT  # Let's be neat.
        self.output_dir = self.settings.base_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        # You need to call login() and run(), but we won't: it makes testing easier.

    def login(self):
        """Log in and set the necessary tokens.

        Should be called right after initialising the class. It is a separate
        method to make testing easier.

        """
        logger.info("Logging in on %s as user %s...", API_HOST, self.settings.username)
        auth_api = openapi_client.AuthApi(self.api_client)
        user_plus_password = openapi_client.Authenticate(
            username=self.settings.username, password=self.settings.password
        )
        try:
            tokens = auth_api.auth_token_create(user_plus_password)
        except openapi_client.exceptions.ApiException as e:
            status = getattr(e, "status", None)
            if status == 401:
                msg = (
                    f"Authentication of '{self.settings.username}' failed on "
                    f"{API_HOST} with the given password"
                )
                raise AuthenticationError(msg) from e
            logger.debug("Error isn't a 401, so we re-raise it.")
            raise
        # Set tokens on the configuration (which is used by self.api_client).
        self.configuration.api_key["Authorization"] = tokens.access
        self.configuration.api_key_prefix["Authorization"] = "Bearer"

    def run(self):
        """Main method

        Should be called as second method right after ``.login()`` and
        ``__init__()``. It is a separate method to make testing easier.

        We call helper methods (``._find_model()``) for all the individual
        steps. This makes it easy to add more steps later. These methods
        should not themselves set any parameters on ``self``: if something is
        needed later on (like ``saved_state_id``), it should be returned. The
        ``.run()`` method is the one that should keep track of those
        variables. Otherwise methods become harder to test in isolation.

        """
        self.simulations_api = openapi_client.SimulationsApi(self.api_client)
        self.threedimodels_api = openapi_client.ThreedimodelsApi(self.api_client)
        model_id = self._find_model()
        self.simulation_id, self.simulation_url = self._create_simulation(model_id)

        laterals_csv = self.settings.base_dir / "input" / "lateral.csv"
        if laterals_csv.exists():
            laterals = utils.lateral_timeseries(laterals_csv, self.settings)
            self._add_laterals(laterals)
        else:
            logger.info("No lateral timeseries found at %s, skipping.", laterals_csv)

        saved_state_id_file = (
            self.settings.base_dir / "states" / SAVED_STATE_ID_FILENAME
        )
        if self.settings.save_state:
            self._add_initial_state(saved_state_id_file)
            self.saved_state_id = self._prepare_initial_state()
        else:
            logger.info("Saved state not enabled in the configuration, skipping.")

        rain_file = self.settings.base_dir / "input" / "precipitation.nc"
        if rain_file.exists():
            rain_raster_netcdf = utils.write_netcdf_with_time_indexes(
                rain_file, self.settings
            )
            self._add_rain(rain_raster_netcdf)
        else:
            logger.info("No rain file found at %s, skipping.", rain_file)

        evaporation_file = self.settings.base_dir / "input" / "evaporation.nc"
        if evaporation_file.exists():
            evaporation_raster_netcdf = utils.write_netcdf_with_time_indexes(
                evaporation_file, self.settings
            )
            self._add_evaporation(evaporation_raster_netcdf)
        else:
            logger.info("No evaporation file found at %s, skipping.", evaporation_file)

        if self.settings.lizard_results_scenario_name:
            self._process_basic_lizard_results()
        else:
            logger.info("Not processing basic results in Lizard")

        self._run_simulation()
        self._download_results()
        if self.settings.save_state:
            self._write_saved_state_id(saved_state_id_file)
        self._process_results()
        logger.info("Done.")

    def _find_model(self) -> int:
        """Return model ID based on the model revision in the settings."""
        logger.debug(
            "Searching model based on revision=%s...", self.settings.modelrevision
        )
        threedimodels_result = self.threedimodels_api.threedimodels_list(
            slug__contains=self.settings.modelrevision
        )
        results = threedimodels_result.results
        if not results:
            raise NotFoundError(
                "Model with revision={self.settings.modelrevision} not found"
            )
        id = results[0].id
        url = results[0].url
        logger.info("Simulation uses model %s", url)
        return id

    def _create_simulation(self, model_id: int) -> Tuple[int, str]:
        """Return id and url of created simulation."""
        data = {}
        data["name"] = self.settings.simulationname
        data["threedimodel"] = str(model_id)
        data["organisation"] = self.settings.organisation
        data["start_datetime"] = self.settings.start.isoformat()
        data["duration"] = str(self.settings.duration)
        logger.debug("Creating simulation with these settings: %s", data)

        simulation = self.simulations_api.simulations_create(data)
        logger.info("Simulation %s has been created", simulation.url)
        return simulation.id, simulation.url

    def _add_laterals(self, laterals):
        """Upload lateral timeseries and wait for them to be processed."""
        still_to_process: List[int] = []
        logger.info("Uploading %s lateral timeseries...", len(laterals))

        for name, timeserie in laterals.items():
            first_offset = timeserie[0].offset  # TODO: by definition, this is 0???
            lateral = self.simulations_api.simulations_events_lateral_timeseries_create(
                simulation_pk=self.simulation_id,
                data={
                    "offset": first_offset,
                    "interpolate": False,
                    "values": timeserie,
                    "units": "m3/s",
                    "connection_node": name,
                },
            )
            logger.debug("Added lateral timeserie '%s': %s", name, lateral.url)
            still_to_process.append(lateral.id)

        logger.debug("Waiting for laterals to be processed...")
        while True:
            time.sleep(2)
            for id in still_to_process:
                lateral = (
                    self.simulations_api.simulations_events_lateral_timeseries_read(
                        simulation_pk=self.simulation_id, id=id
                    )
                )
                if lateral.state.lower() == "processing":
                    logger.debug("Lateral %s is still being processed.", lateral.url)
                    continue
                elif lateral.state.lower() == "invalid":
                    msg = f"Lateral {lateral.url} is invalid according to the server."
                    raise InvalidDataError(msg)
                elif lateral.state.lower() == "error":
                    state_description = lateral.state_description
                    msg = f"Server returned an error. Response is: {state_description}"
                    raise InvalidDataError(msg)
                elif lateral.state.lower() == "valid":
                    logger.debug("Lateral %s is valid.", lateral.url)
                    still_to_process.remove(id)

            if not still_to_process:
                return

    def _add_initial_state(self, saved_state_id_file: Path):
        # TODO explain rationale. (likewise for the other methods).
        if not saved_state_id_file.exists():
            msg = f"Saved state id file {saved_state_id_file} not found"
            if self.allow_missing_saved_state:
                logger.warn(msg)
                return
            else:
                raise utils.MissingFileException(msg)
        saved_state_id: str = saved_state_id_file.read_text().strip()
        logger.info("Simulation will use initial state %s", saved_state_id)
        try:
            self.simulations_api.simulations_initial_saved_state_create(
                self.simulation_id, data={"saved_state": saved_state_id}
            )
        except openapi_client.exceptions.ApiException as e:
            if e.status == 400:
                logger.debug("Saved state setting error: %s", str(e))
                msg = (
                    f"Setting initial state to saved state id={saved_state_id} failed. "
                    f"The error response was {e.body}, perhaps use "
                    f"--allow-missing-saved-state initially?"
                )
                if self.allow_missing_saved_state:
                    logger.warn(msg)
                    return
                else:
                    raise MissingSavedStateError(msg) from e
            logger.debug("Error isn't a 400, so we re-raise it.")
            raise

    def _prepare_initial_state(self) -> int:
        """Instruct 3di to save the state afterwards and return its ID."""
        expiry_timestamp = datetime.datetime.now() + datetime.timedelta(
            days=self.settings.saved_state_expiry_days
        )
        saved_state = self.simulations_api.simulations_create_saved_states_timed_create(
            self.simulation_id,
            data={
                "name": self.settings.simulationname,
                "time": self.settings.duration,
                "expiry": expiry_timestamp.isoformat(),
            },
        )
        logger.info("Saved state will be stored: %s", saved_state.url)
        return saved_state.id

    def _add_rain(self, rain_raster_netcdf: Path):
        """Upload rain raster netcdf file and wait for it to be processed."""
        logger.info("Uploading rain rasters...")
        rain_api_call = (
            self.simulations_api.simulations_events_rain_rasters_netcdf_create(
                self.simulation_id, data={"filename": rain_raster_netcdf.name}
            )
        )
        log_url = rain_api_call.put_url.split("?")[0]  # Strip off aws credentials.
        with rain_raster_netcdf.open("rb") as f:
            response = requests.put(rain_api_call.put_url, data=f)
            response.raise_for_status()
        logger.debug("Added rain raster to %s", log_url)

        logger.debug("Waiting for rain raster to be processed...")
        while True:
            time.sleep(2)
            upload_status = (
                self.simulations_api.simulations_events_rain_rasters_netcdf_list(
                    self.simulation_id
                )
            )
            state = upload_status.results[0].file.state
            if state.lower() == "processing":
                logger.debug("Rain raster is still being processed.")
                continue
            elif state.lower() == "invalid":
                msg = f"Rain raster upload (to {log_url}) is invalid according to the server."
                raise InvalidDataError(msg)
            elif state.lower() == "error":
                state_description = upload_status.results[0].file.state_description
                msg = f"Server returned an error. Response is: {state_description}"
                raise InvalidDataError(msg)
            elif state.lower() == "processed":
                logger.debug("Rain raster %s has been processed.", log_url)
                return
            else:
                logger.debug("Unknown state: %s", state)

    # TODO: virtually the same as _add_rain()
    # Perhaps a list with dicts as config? precipitation, evaporation.
    # Can it be done through
    # https://api.3di.live/v3.0/simulations/1673/events/rain/rasters/netcdf/ ?
    def _add_evaporation(self, evaporation_raster_netcdf: Path):
        """Upload evaporation raster netcdf file and wait for it to be processed."""
        logger.info("Uploading evaporation rasters...")
        evaporation_api_call = (
            self.simulations_api.simulations_events_sources_sinks_rasters_netcdf_create(
                self.simulation_id, data={"filename": evaporation_raster_netcdf.name}
            )
        )
        log_url = evaporation_api_call.put_url.split("?")[
            0
        ]  # Strip off aws credentials.
        with evaporation_raster_netcdf.open("rb") as f:
            response = requests.put(evaporation_api_call.put_url, data=f)
            response.raise_for_status()
        logger.debug("Added evaporation raster to %s", log_url)

        logger.debug("Waiting for evaporation raster to be processed...")
        while True:
            time.sleep(2)
            upload_status = self.simulations_api.simulations_events_sources_sinks_rasters_netcdf_list(
                self.simulation_id
            )
            state = upload_status.results[0].file.state
            if state.lower() == "processing":
                logger.debug("Evaporation raster is still being processed.")
                continue
            elif state.lower() == "invalid":
                msg = f"Evaporation raster upload (to {log_url}) is invalid according to the server."
                raise InvalidDataError(msg)
            elif state.lower() == "error":
                state_description = upload_status.results[0].file.state_description
                msg = f"Server returned an error. Response is: {state_description}"
                raise InvalidDataError(msg)
            elif state.lower() == "processed":
                logger.debug("Evaporation raster %s has been processed.", log_url)
                return
            else:
                logger.debug("Unknown state: %s", state)

    def _run_simulation(self):
        """Start simulation and wait for it to finish."""
        start_data = {"name": "start"}
        self.simulations_api.simulations_actions_create(
            self.simulation_id, data=start_data
        )
        logger.info("Simulation %s has been started.", self.simulation_url)

        start_time = time.time()
        while True:
            time.sleep(SIMULATION_STATUS_CHECK_INTERVAL)
            try:
                simulation_status = self.simulations_api.simulations_status_list(
                    self.simulation_id
                )
            except socket.gaierror as e:
                logger.debug(e)
                logger.warning("Hopefully temporary local network hickup")
                continue
            if simulation_status.name == "finished":
                logger.info("Simulation has finished")
                return
            running_time = round(time.time() - start_time)
            logger.info(
                "%ss: simulation is still running (status=%s)",
                running_time,
                simulation_status.name,
            )
            # Note: status 'initialized' actually means 'running'.

    def _download_results(self):
        logger.info("Downloading results into %s...", self.output_dir)
        simulation_results = self.simulations_api.simulations_results_files_list(
            self.simulation_id
        ).results
        logger.debug("All simulation results: %s", simulation_results)
        desired_results = [
            f"log_files_sim_{self.simulation_id}.zip",
            "results_3di.nc",
        ]
        available_results = {
            simulation_result.filename.lower(): simulation_result
            for simulation_result in simulation_results
        }
        for desired_result in desired_results:
            if desired_result not in available_results:
                logger.error("Desired result file %s isn't available.", desired_result)
                continue
            resource = self.simulations_api.simulations_results_files_download(
                available_results[desired_result].id, self.simulation_id
            )
            target = self.output_dir / desired_result
            with open(target, "wb") as f:
                response = requests.get(resource.get_url)
                response.raise_for_status()
                f.write(response.content)
            logger.info("Downloaded %s", target)

    def _process_basic_lizard_results(self):

        data = {
            "scenario_name": self.settings.lizard_results_scenario_name,
            "process_basic_results": True,
        }
        if self.settings.lizard_results_scenario_uuid:
            data["result_uuid"] = self.settings.lizard_results_scenario_uuid

        self.simulations_api.simulations_results_post_processing_lizard_basic_create(
            simulation_pk=self.simulation_id, data=data
        )

        logger.info(
            "Basic lizard results will be processed as %s",
            self.settings.lizard_results_scenario_name,
        )

    def _write_saved_state_id(self, saved_state_id_file):
        """Write ID of the saved style to the file for later usage.

        3Di was instructed to save the state previously, now we write its
        previously-determined ID to a file.

        """
        saved_state_id_file.write_text(str(self.saved_state_id))
        logger.info(
            "Wrote saved state id (%s) to %s", self.saved_state_id, saved_state_id_file
        )

    def _process_results(self):
        # Input files
        gridadmin_file = self.settings.base_dir / "model" / "gridadmin.h5"
        if not gridadmin_file.exists():
            raise utils.MissingFileException(
                "Gridadmin file %s not found", gridadmin_file
            )
        results_file = self.output_dir / "results_3di.nc"
        if not results_file.exists():
            raise utils.MissingFileException("Results file %s not found", results_file)
        open_water_input_file = self.settings.base_dir / "input" / "ow.nc"
        if not open_water_input_file.exists():
            raise utils.MissingFileException(
                "Open water input file %s not found", open_water_input_file
            )

        results = GridH5ResultAdmin(str(gridadmin_file), str(results_file))
        times = results.nodes.timestamps[()] + self.settings.start.timestamp()
        times = times.astype("datetime64[s]")
        times = pd.Series(times).dt.round("10 min")
        endtime = results.nodes.timestamps[-1]

        if results.has_pumpstations:
            pump_id = results.pumps.display_name.astype("U13")
            discharges = results.pumps.timeseries(start_time=0, end_time=endtime).data[
                "q_pump"
            ]
            discharges_dataframe = pd.DataFrame(
                discharges, index=times, columns=pump_id
            )
            params = ["Q.sim" for x in range(len(discharges_dataframe.columns))]

            discharges_dataframe.columns = pd.MultiIndex.from_arrays(
                [pump_id, pump_id, params]
            )
            discharges_csv_output = self.output_dir / "discharges.csv"
            discharges_dataframe.to_csv(
                discharges_csv_output, index=True, header=True, sep=","
            )
            logger.info(
                "Simulated pump discharges have been exported to %s",
                discharges_csv_output,
            )

        open_water_input_file = self.settings.base_dir / "input" / "ow.nc"
        open_water_output_file = self.settings.base_dir / "output" / "ow.nc"
        converted_netcdf = utils.write_netcdf_with_time_indexes(
            open_water_input_file, self.settings
        )
        # converted_netcdf is a temp file, so move it to the correct spot.
        converted_netcdf.replace(open_water_output_file)
        logger.debug("Started open water output file %s", open_water_output_file)
        dset = netCDF4.Dataset(open_water_output_file, "a")
        s1 = (
            results.nodes.subset("2D_OPEN_WATER")
            .timeseries(start_time=0, end_time=endtime)
            .s1
        )
        dset["Mesh2D_s1"][:, :] = s1
        dset.close()
        logger.info("Wrote open water output file %s", open_water_output_file)
