"""Constants for the Ollama Vision integration."""
import logging

DOMAIN = "ollama_vision"
LOGGER = logging.getLogger(__package__)

CONF_OLLAMA_HOST = "ollama_host"
CONF_OLLAMA_MODEL = "ollama_model"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "moondream"