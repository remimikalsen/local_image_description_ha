"""The Ollama Vision integration."""
import logging
import voluptuous as vol
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_NAME, Platform
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_MODEL,
    ATTR_IMAGE_URL,
    ATTR_PROMPT,
    ATTR_IMAGE_NAME,
    ATTR_DEVICE_ID,
    SERVICE_ANALYZE_IMAGE,
    EVENT_IMAGE_ANALYZED,
    ATTR_USE_TEXT_MODEL,
    ATTR_TEXT_PROMPT,
    CONF_TEXT_MODEL_ENABLED,
    CONF_TEXT_HOST,
    CONF_TEXT_PORT,
    CONF_TEXT_MODEL,
    DEFAULT_TEXT_PORT,
    DEFAULT_TEXT_MODEL,
    CONF_TEXT_KEEPALIVE,
    DEFAULT_KEEPALIVE,
    CONF_VISION_KEEPALIVE,
    DEFAULT_PROMPT,
    DEFAULT_TEXT_PROMPT
)
from .api import OllamaClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Service schema
ANALYZE_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMAGE_URL): cv.string,
        vol.Optional(ATTR_PROMPT, default=DEFAULT_PROMPT): cv.string,
        vol.Required(ATTR_IMAGE_NAME): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_USE_TEXT_MODEL, default=False): cv.boolean,
        vol.Optional(ATTR_TEXT_PROMPT, default=DEFAULT_TEXT_PROMPT): cv.string,
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ollama Vision component."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]["pending_sensors"] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Vision from a config entry."""
    host = entry.data.get(CONF_HOST) or entry.options.get(CONF_HOST)
    port = entry.data.get(CONF_PORT) or entry.options.get(CONF_PORT)
    model = entry.data.get(CONF_MODEL) or entry.options.get(CONF_MODEL)
    name = entry.data.get(CONF_NAME)
    vision_keepalive = entry.data.get(CONF_VISION_KEEPALIVE) or entry.options.get(CONF_VISION_KEEPALIVE, DEFAULT_KEEPALIVE)
    
    # Get text model settings
    text_model_enabled = entry.data.get(CONF_TEXT_MODEL_ENABLED) or entry.options.get(CONF_TEXT_MODEL_ENABLED, False)
    text_host = None
    text_port = None
    text_model = None
    text_keepalive = DEFAULT_KEEPALIVE
    
    if text_model_enabled:
        text_host = entry.data.get(CONF_TEXT_HOST) or entry.options.get(CONF_TEXT_HOST)
        text_port = entry.data.get(CONF_TEXT_PORT) or entry.options.get(CONF_TEXT_PORT, DEFAULT_TEXT_PORT)
        text_model = entry.data.get(CONF_TEXT_MODEL) or entry.options.get(CONF_TEXT_MODEL, DEFAULT_TEXT_MODEL)
        text_keepalive = entry.data.get(CONF_TEXT_KEEPALIVE) or entry.options.get(CONF_TEXT_KEEPALIVE, DEFAULT_KEEPALIVE)
    
    client = OllamaClient(host, port, model, text_host, text_port, text_model, vision_keepalive, text_keepalive)
    
    # Store the client in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "sensors": {},
        "config": {
            "host": host,
            "port": port,
            "model": model,
            "name": name,
            CONF_TEXT_MODEL_ENABLED: text_model_enabled,
            CONF_TEXT_HOST: text_host,
            CONF_TEXT_PORT: text_port,
            CONF_TEXT_MODEL: text_model,
            CONF_TEXT_MODEL: text_model,
            CONF_TEXT_KEEPALIVE: text_keepalive
        },
        "device_info": {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Ollama Vision {name}",
            "manufacturer": "Ollama",
            "model": model,
            "sw_version": "0.1.1",
            "configuration_url": f"http://{host}:{port}",
        }
    }
    
    # Rest of the function remains the same

    # Create service handler wrapper
    @callback
    def async_handle_service(call):
        """Handle the service call."""
        hass.async_create_task(handle_analyze_image(hass, call))
    
    # Register service with the wrapper
    hass.services.async_register(
        DOMAIN,
        SERVICE_ANALYZE_IMAGE,
        async_handle_service,
        schema=ANALYZE_IMAGE_SCHEMA,
    )
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

# Define the analyze_image service outside of async_setup_entry
async def handle_analyze_image(hass, call):
    """Handle the analyze_image service call."""
    image_url = call.data.get(ATTR_IMAGE_URL)
    vision_prompt = call.data.get(ATTR_PROMPT, DEFAULT_PROMPT)
    image_name = call.data.get(ATTR_IMAGE_NAME)
    device_id = call.data.get(ATTR_DEVICE_ID)
    use_text_model = call.data.get(ATTR_USE_TEXT_MODEL, False)
    text_prompt = call.data.get(ATTR_TEXT_PROMPT, DEFAULT_TEXT_PROMPT)
    
    # Determine which integration to use based on device_id
    entry_id_to_use = None
    
    if device_id:
        # Use device registry to find the config entry
        device_registry = async_get_device_registry(hass)
        device = device_registry.async_get(device_id)
        
        if device and device.config_entries:
            # Get the first config entry associated with this device
            # that belongs to our domain
            for entry_id in device.config_entries:
                if entry_id in hass.data[DOMAIN]:
                    entry_id_to_use = entry_id
                    break
    
    if not entry_id_to_use:
        # If no device_id specified or device_id not found
        if len(hass.data[DOMAIN]) > 1 and not device_id:
            _LOGGER.warning(
                "Multiple Ollama Vision instances found but no device_id specified. "
                "Using first available. Specify device_id parameter to target a specific instance."
            )
        
        entry_id_to_use = list(hass.data[DOMAIN].keys())[0]
    
    client_to_use = hass.data[DOMAIN][entry_id_to_use]["client"]
    
    # Analyze the image using the selected client
    vision_description = await client_to_use.analyze_image(image_url, vision_prompt)
    
    if vision_description is None:
        raise HomeAssistantError("Failed to analyze image")
    
    # Determine if we should use the text model for elaboration
    config = hass.data[DOMAIN][entry_id_to_use]["config"]
    text_model_enabled = config.get(CONF_TEXT_MODEL_ENABLED, False)
    
    # Only elaborate if both the service call requests it and the config has it enabled
    final_description = vision_description
    if use_text_model and text_model_enabled:
        text_prompt_formatted = text_prompt.format(description=vision_description)
        final_description = await hass.data[DOMAIN][entry_id_to_use]["client"].elaborate_text(
            vision_description, text_prompt_formatted
        )
    
    # Store sensor data persistently
    pending_sensors = hass.data[DOMAIN].setdefault("pending_sensors", {}).setdefault(entry_id_to_use, {})

    pending_sensors[image_name] = {
        "description": vision_description,
        "image_url": image_url,
        "prompt": vision_prompt,
        "unique_id": f"{DOMAIN}_{entry_id_to_use}_{image_name}",
        "final_description": final_description if (use_text_model and text_model_enabled) else None,
        "text_prompt": text_prompt_formatted if (use_text_model and text_model_enabled) else None,
        "used_text_model": use_text_model and text_model_enabled
    }

    # Fire event to notify platform to create or update sensor
    hass.bus.async_fire(f"{DOMAIN}_create_sensor", {
        "entry_id": entry_id_to_use,
        "image_name": image_name
    })

    # Fire an event for external use
    event_data = {
        "image_name": image_name,
        "description": vision_description,
        "image_url": image_url,
        "integration_id": entry_id_to_use,
        "used_text_model": use_text_model and text_model_enabled
    }

    hass.bus.async_fire(EVENT_IMAGE_ANALYZED, event_data)    


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload sensor platform
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Check if this is the last instance of the integration
        if len(hass.data[DOMAIN]) <= 1:
            # Unregister service if this is the last instance
            hass.services.async_remove(DOMAIN, SERVICE_ANALYZE_IMAGE)
        
        # Remove data for this entry
        hass.data[DOMAIN].pop(entry.entry_id)
        if entry.entry_id in hass.data[DOMAIN].get("pending_sensors", {}):
            hass.data[DOMAIN]["pending_sensors"].pop(entry.entry_id)
    
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
