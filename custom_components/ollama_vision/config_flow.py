"""Config flow for Ollama Vision integration."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_OLLAMA_HOST,
    CONF_OLLAMA_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_MODEL,
)


class OllamaVisionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Vision."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Handle the initial step."""
        data_schema = vol.Schema({
            vol.Required(CONF_OLLAMA_HOST, default=DEFAULT_OLLAMA_HOST): str,
            vol.Required(CONF_OLLAMA_MODEL, default=DEFAULT_MODEL): str,
        })

        if user_input is not None:
            # You could add validation here before creating the entry
            # For example, try to connect to the Ollama host

            return self.async_create_entry(
                title=f"Ollama Vision ({user_input[CONF_OLLAMA_HOST]})",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OllamaVisionOptionsFlow:
        """Get the options flow for this handler."""
        return OllamaVisionOptionsFlow(config_entry)


class OllamaVisionOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Manage the options."""
        # Use current options or fallback to data
        current_host = self.config_entry.options.get(
            CONF_OLLAMA_HOST,
            self.config_entry.data.get(CONF_OLLAMA_HOST, DEFAULT_OLLAMA_HOST)
        )
        current_model = self.config_entry.options.get(
            CONF_OLLAMA_MODEL,
            self.config_entry.data.get(CONF_OLLAMA_MODEL, DEFAULT_MODEL)
        )

        data_schema = vol.Schema({
            vol.Required(CONF_OLLAMA_HOST, default=current_host): str,
            vol.Required(CONF_OLLAMA_MODEL, default=current_model): str,
        })

        if user_input is not None:
            # Save new options
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )