"""Constants for the Ollama Vision integration."""

DOMAIN = "ollama_vision"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_MODEL = "model"

# Default values
DEFAULT_PORT = 11434
DEFAULT_MODEL = "moondream"

# Service call constants
SERVICE_ANALYZE_IMAGE = "analyze_image"
ATTR_IMAGE_URL = "image_url"
ATTR_PROMPT = "prompt"
ATTR_IMAGE_NAME = "image_name"
ATTR_INTEGRATION_ID = "integration_id"
ATTR_DEVICE_ID = "device_id"

# Event constants
EVENT_IMAGE_ANALYZED = "ollama_vision_image_analyzed"