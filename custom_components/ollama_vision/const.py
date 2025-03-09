"""Constants for the Ollama Vision integration."""

DOMAIN = "ollama_vision"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_MODEL = "model"
DEFAULT_KEEPALIVE = -1

# Default values
DEFAULT_PORT = 11434
DEFAULT_MODEL = "moondream"
CONF_VISION_KEEPALIVE = "vision_keepalive"

# Service call constants
SERVICE_ANALYZE_IMAGE = "analyze_image"
ATTR_IMAGE_URL = "image_url"
ATTR_PROMPT = "prompt"
ATTR_IMAGE_NAME = "image_name"
ATTR_DEVICE_ID = "device_id"

# Event constants
EVENT_IMAGE_ANALYZED = "ollama_vision_image_analyzed"

# Textual model (optional)
CONF_TEXT_MODEL_ENABLED = "text_model_enabled"
CONF_TEXT_HOST = "text_host"
CONF_TEXT_PORT = "text_port"
CONF_TEXT_MODEL = "text_model"
DEFAULT_TEXT_PORT = 11434
DEFAULT_TEXT_MODEL = "llama3.1"
CONF_TEXT_KEEPALIVE = "text_keepalive"

# Textual model service call constants
ATTR_USE_TEXT_MODEL = "use_text_model"
ATTR_TEXT_PROMPT = "text_prompt"
