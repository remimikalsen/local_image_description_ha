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
    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_OLLAMA_HOST, default=DEFAULT_OLLAMA_HOST): str,
            vol.Required(CONF_OLLAMA_MODEL, default=DEFAULT_MODEL): str,
        })

        if user_input is not None:
            return self.async_create_entry(
                title=f"Ollama Vision ({user_input[CONF_OLLAMA_HOST]})", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
