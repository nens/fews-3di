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

import logging
import openapi_client


API_HOST = "https://api.3di.live/v3.0"
USER_AGENT = "fews-3di (https://github.com/nens/fews-3di/)"


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ThreediSimulation:
    """Wrapper for a set of 3di API calls."""

    api_client: openapi_client.ApiClient
    configuration: openapi_client.Configuration
    settings: utils.Settings
    simulations_api: openapi_client.SimulationsApi
    simulation_id: int

    def __init__(self, settings):
        """Set up a 3di API connection."""
        self.settings = settings
        self.configuration = openapi_client.Configuration(host=API_HOST)
        self.api_client = openapi_client.ApiClient(self.configuration)
        self.api_client.user_agent = USER_AGENT  # Let's be neat.
        # You need to call login() here, but we won't: it makes testing easier.

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
            raise  # Simply re-raise.
        # Set tokens on the configuration (which is used by self.api_client).
        self.configuration.api_key["Authorization"] = tokens.access
        self.configuration.api_key_prefix["Authorization"] = "Bearer"

    def run(self):
        """Main method, should be called after login()."""
        model_id = self._find_model()
        self.simulations_api = openapi_client.SimulationsApi(self.api_client)
        self.simulation_id = self._create_simulation(model_id)

        laterals_csv = self.settings.base_dir / "input" / "lateral.csv"
        laterals = utils.lateral_timeseries(laterals_csv, self.settings)
        print(len(laterals))
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

    def _create_simulation(self, model_id: int) -> int:
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
        return simulation.id
