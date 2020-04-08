""""
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


class ThreediSimulation:
    """Wrapper for a set of 3di API calls."""

    api_client: openapi_client.ApiClient
    configuration: openapi_client.Configuration
    settings: utils.Settings

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
        pass
