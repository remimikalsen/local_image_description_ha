"""Config flow for Ollama Vision integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_MODEL,
    DEFAULT_PORT,
    DEFAULT_MODEL,
)

_LOGGER = logging.getLogger(__name__)

class OllamaVisionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Vision."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Test connection to Ollama
            try:
                session = aiohttp.ClientSession()
                api_url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/api/version"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        await session.close()
                        return self.async_create_entry(
                            title=user_input[CONF_NAME],
                            data=user_input
                        )
                    errors["base"] = "cannot_connect"
                await session.close()
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form for user input
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_MODEL, default=DEFAULT_MODEL): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OllamaVisionOptionsFlow(config_entry)


class OllamaVisionOptionsFlow(config_entries.OptionsFlow):
    """Handle a option flow for Ollama Vision."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, 
                        default=options.get(CONF_HOST, self.config_entry.data.get(CONF_HOST))
                    ): str,
                    vol.Required(
                        CONF_PORT, 
                        default=options.get(CONF_PORT, self.config_entry.data.get(CONF_PORT, DEFAULT_PORT))
                    ): int,
                    vol.Required(
                        CONF_MODEL, 
                        default=options.get(CONF_MODEL, self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL))
                    ): str,
                }
            ),
        )