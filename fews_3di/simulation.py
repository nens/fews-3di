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
from typing import List
from typing import Tuple

import logging
import openapi_client
import requests
import time


API_HOST = "https://api.3di.live/v3.0"
USER_AGENT = "fews-3di (https://github.com/nens/fews-3di/)"
SIMULATION_STATUS_CHECK_INTERVAL = 30

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidDataError(Exception):
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

    api_client: openapi_client.ApiClient
    configuration: openapi_client.Configuration
    settings: utils.Settings
    simulations_api: openapi_client.SimulationsApi
    simulation_id: int
    simulation_url: str

    def __init__(self, settings):
        """Set up a 3di API connection."""
        self.settings = settings
        self.configuration = openapi_client.Configuration(host=API_HOST)
        self.api_client = openapi_client.ApiClient(self.configuration)
        self.api_client.user_agent = USER_AGENT  # Let's be neat.
        # You need to call login(), but we won't: it makes testing easier.

    def login(self):
        """Log in and set the necessary tokens.

        Called from the init. It is a separate method to make testing easier.
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
        """Main method, should be called after login()."""
        model_id = self._find_model()
        self.simulations_api = openapi_client.SimulationsApi(self.api_client)
        self.simulation_id, self.simulation_url = self._create_simulation(model_id)

        laterals_csv = self.settings.base_dir / "input" / "lateral.csv"
        laterals = utils.lateral_timeseries(laterals_csv, self.settings)
        self._add_laterals(laterals)

        rain_file = self.settings.base_dir / "input" / "precipitation.nc"
        rain_raster_netcdf = utils.convert_rain_events(
            rain_file, self.settings, self.simulation_id
        )
        self._add_rain(rain_raster_netcdf)

        evaporation_file = self.settings.base_dir / "input" / "evaporation.nc"
        evaporation_raster_netcdf = utils.convert_evaporation(
            evaporation_file, self.settings, self.simulation_id
        )
        self._add_evaporation(evaporation_raster_netcdf)

        self._run_simulation()
        self._download_results()
        print("TODO")

    def _find_model(self) -> int:
        """Return model ID based on the model revision in the settings."""
        logger.debug(
            "Searching model based on revision=%s...", self.settings.modelrevision
        )
        threedimodels_api = openapi_client.ThreedimodelsApi(self.api_client)
        threedimodels_result = threedimodels_api.threedimodels_list(
            slug__contains=self.settings.modelrevision
        )
        if not threedimodels_result.results:
            raise NotFoundError(
                "Model with revision={self.settings.modelrevision} not found"
            )
        id = threedimodels_result.results[0].id
        url = threedimodels_result.results[0].url
        logger.info("Simulation uses model %s", url)
        return id

    def _create_simulation(self, model_id: int) -> Tuple[int, str]:
        """Return id and url of created simulation."""
        data = {}
        data["name"] = self.settings.simulationname
        data["threedimodel"] = str(model_id)
        data["organisation"] = self.settings.organisation
        data["start_datetime"] = self.settings.start.isoformat()
        # TODO: end_datetime is also possible!
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
                lateral = self.simulations_api.simulations_events_lateral_timeseries_read(
                    simulation_pk=self.simulation_id, id=id
                )
                if lateral.state.lower() == "processing":
                    logger.debug("Lateral %s is still being processed.", lateral.url)
                    continue
                elif lateral.state.lower() == "invalid":
                    msg = f"Lateral {lateral.url} is invalid according to the server."
                    raise InvalidDataError(msg)
                elif lateral.state.lower() == "valid":
                    logger.debug("Lateral %s is valid.", lateral.url)
                    still_to_process.remove(id)

            if not still_to_process:
                return

    def _add_rain(self, rain_raster_netcdf: Path):
        """Upload rain raster netcdf file and wait for it to be processed."""
        logger.info("Uploading rain rasters...")
        rain_api_call = self.simulations_api.simulations_events_rain_rasters_netcdf_create(
            self.simulation_id, data={"filename": rain_raster_netcdf.name}
        )
        log_url = rain_api_call.put_url.split("?")[0]  # Strip off aws credentials.
        with rain_raster_netcdf.open("rb") as f:
            response = requests.put(rain_api_call.put_url, data=f)
            response.raise_for_status()
        logger.debug("Added rain raster to %s", log_url)

        logger.debug("Waiting for rain raster to be processed...")
        while True:
            time.sleep(2)
            upload_status = self.simulations_api.simulations_events_rain_rasters_netcdf_list(
                self.simulation_id
            )
            state = upload_status.results[0].file.state
            if state.lower() == "processing":
                logger.debug("Rain raster is still being processed.")
                continue
            elif state.lower() == "invalid":
                msg = f"Rain raster upload (to {log_url}) is invalid according to the server."
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
        evaporation_api_call = self.simulations_api.simulations_events_sources_sinks_rasters_netcdf_create(
            self.simulation_id, data={"filename": evaporation_raster_netcdf.name}
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
            simulation_status = self.simulations_api.simulations_status_list(
                self.simulation_id
            )
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
        output_dir = self.settings.base_dir / "output"
        output_dir.mkdir(exist_ok=True)
        logger.info("Downloading results into %s...", output_dir)
        simulation_results = self.simulations_api.simulations_results_files_list(
            self.simulation_id
        ).results
        logger.debug("All simulation results: %s", simulation_results)
        desired_results = [
            "simulation.log",
            "flow_summary.log",
            f"log_files_sim_{self.simulation_id}.zip",
            "results_3di.nc",
        ]
        available_results = {
            simulation_result.filename.lower(): simulation_result
            for simulation_result in simulation_results
        }
        for desired_result in desired_results:
            if desired_result not in available_results:
                logger.warning(
                    "Desired result file %s isn't available.", desired_result
                )
                continue
            resource = self.simulations_api.simulations_results_files_download(
                available_results[desired_result].id, self.simulation_id
            )
            target = output_dir / desired_result
            with open(target, "wb") as f:
                response = requests.get(resource.get_url)
                response.raise_for_status()
                f.write(response.content)
            logger.info("Downloaded %s", target)
