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
    CONF_TEXT_MODEL_ENABLED,
    CONF_TEXT_HOST,
    CONF_TEXT_PORT,
    CONF_TEXT_MODEL,
    DEFAULT_TEXT_PORT,
    DEFAULT_TEXT_MODEL,
    CONF_VISION_KEEPALIVE,
    DEFAULT_KEEPALIVE,
    CONF_TEXT_KEEPALIVE
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
            # If text model is enabled, ensure all text model fields are provided
            if user_input.get(CONF_TEXT_MODEL_ENABLED):
                if not user_input.get(CONF_TEXT_HOST):
                    errors["text_host"] = "required"
                else:
                    # Test connection to both Ollama instances
                    try:
                        failed = False
                        session = aiohttp.ClientSession()
                        api_url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/api/version"
                        async with session.get(api_url) as response:
                            if response.status != 200:
                                errors["base"] = "cannot_connect"
                                failed = True

                        api_url = f"http://{user_input[CONF_TEXT_HOST]}:{user_input[CONF_TEXT_PORT]}/api/version"
                        async with session.get(api_url) as response:
                            if response.status != 200:
                                errors["base"] = "cannot_connect"
                                failed = True
                        
                        await session.close()
                        
                        if not failed:
                            return self.async_create_entry(
                            title=user_input[CONF_NAME],
                                data=user_input
                            )
                        
                    except aiohttp.ClientError:
                        errors["base"] = "cannot_connect"
                    except Exception:  # pylint: disable=broad-except
                        _LOGGER.exception("Unexpected exception")
                        errors["base"] = "unknown"

            else:
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
        data_schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_MODEL, default=DEFAULT_MODEL): str,
            vol.Required(CONF_VISION_KEEPALIVE, default=DEFAULT_KEEPALIVE): int,
            vol.Optional(CONF_TEXT_MODEL_ENABLED, default=False): bool,
        })
        
        # Add text model fields conditionally if text model is enabled
        if user_input and user_input.get(CONF_TEXT_MODEL_ENABLED):
            data_schema = data_schema.extend({
                vol.Required(CONF_TEXT_HOST): str,
                vol.Required(CONF_TEXT_PORT, default=DEFAULT_TEXT_PORT): int,
                vol.Required(CONF_TEXT_MODEL, default=DEFAULT_TEXT_MODEL): str,
                vol.Required(CONF_TEXT_KEEPALIVE, default=DEFAULT_KEEPALIVE): int,
            })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
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
        data = self.config_entry.data
        
        # Base schema with vision model settings
        schema = {
            vol.Required(
                CONF_HOST, 
                default=options.get(CONF_HOST, data.get(CONF_HOST))
            ): str,
            vol.Required(
                CONF_PORT, 
                default=options.get(CONF_PORT, data.get(CONF_PORT, DEFAULT_PORT))
            ): int,
            vol.Required(
                CONF_MODEL, 
                default=options.get(CONF_MODEL, data.get(CONF_MODEL, DEFAULT_MODEL))
            ): str,
            vol.Required(
                CONF_VISION_KEEPALIVE,
                default=options.get(CONF_VISION_KEEPALIVE, data.get(CONF_VISION_KEEPALIVE, DEFAULT_KEEPALIVE))
            ): int,
            vol.Optional(
                CONF_TEXT_MODEL_ENABLED,
                default=options.get(CONF_TEXT_MODEL_ENABLED, data.get(CONF_TEXT_MODEL_ENABLED, False))
            ): bool,
        }
        
        # Add text model fields if enabled
        text_enabled = options.get(CONF_TEXT_MODEL_ENABLED, data.get(CONF_TEXT_MODEL_ENABLED, False))
        if text_enabled:
            schema.update({
                vol.Required(
                    CONF_TEXT_HOST,
                    default=options.get(CONF_TEXT_HOST, data.get(CONF_TEXT_HOST, ""))
                ): str,
                vol.Required(
                    CONF_TEXT_PORT,
                    default=options.get(CONF_TEXT_PORT, data.get(CONF_TEXT_PORT, DEFAULT_TEXT_PORT))
                ): int,
                vol.Required(
                    CONF_TEXT_MODEL,
                    default=options.get(CONF_TEXT_MODEL, data.get(CONF_TEXT_MODEL, DEFAULT_TEXT_MODEL))
                ): str,
                vol.Required(
                    CONF_TEXT_KEEPALIVE,
                    default=options.get(CONF_TEXT_KEEPALIVE, data.get(CONF_TEXT_KEEPALIVE, DEFAULT_KEEPALIVE))
                ): int,
            })
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
