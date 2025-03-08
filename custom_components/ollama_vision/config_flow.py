import voluptuous as vol
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_OLLAMA_HOST,
    CONF_OLLAMA_MODEL,
    CONF_DEFAULT_PROMPT,
    CONF_CAMERAS,
    DEFAULT_PROMPT,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_HOST,
)

CAMERA_SCHEMA = vol.Schema({
    vol.Required("camera_name"): str,
    vol.Optional("camera_prompt"): str,
})

class OllamaVisionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Ollama Vision", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_OLLAMA_HOST, default=DEFAULT_OLLAMA_HOST): str,
            vol.Required(CONF_OLLAMA_MODEL, default=DEFAULT_MODEL): str,
            vol.Required(CONF_DEFAULT_PROMPT, default=DEFAULT_PROMPT): str,
            vol.Optional(CONF_CAMERAS, default=[]): vol.All(
                vol.ensure_list, [CAMERA_SCHEMA]
            )
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
