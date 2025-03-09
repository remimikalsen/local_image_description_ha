"""The Ollama Vision integration."""
import logging
import voluptuous as vol
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    ATTR_INTEGRATION_ID,
    ATTR_DEVICE_ID,
    SERVICE_ANALYZE_IMAGE,
    EVENT_IMAGE_ANALYZED,
)
from .api import OllamaClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Service schema
ANALYZE_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_IMAGE_URL): cv.string,
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Required(ATTR_IMAGE_NAME): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ollama Vision component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Vision from a config entry."""
    host = entry.data.get(CONF_HOST) or entry.options.get(CONF_HOST)
    port = entry.data.get(CONF_PORT) or entry.options.get(CONF_PORT)
    model = entry.data.get(CONF_MODEL) or entry.options.get(CONF_MODEL)
    name = entry.data.get(CONF_NAME)
    
    client = OllamaClient(host, port, model)
    
    # Store the client in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "sensors": {},
        "config": {
            "host": host,
            "port": port,
            "model": model,
            "name": name
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
    
    # Register service
    hass.services.async_register(
        DOMAIN,
        SERVICE_ANALYZE_IMAGE,
        lambda call: handle_analyze_image(hass, call),
        schema=ANALYZE_IMAGE_SCHEMA,
    )
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True
    
    # Define the analyze_image service
async def handle_analyze_image(hass, call):
    """Handle the analyze_image service call."""
    image_url = call.data.get(ATTR_IMAGE_URL)
    prompt = call.data.get(ATTR_PROMPT)
    image_name = call.data.get(ATTR_IMAGE_NAME)
    device_id = call.data.get(ATTR_DEVICE_ID)
    
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
    description = await client_to_use.analyze_image(image_url, prompt)
    
    if description is None:
        raise HomeAssistantError("Failed to analyze image")
    
    # Create or update sensor
    sensor_unique_id = f"{DOMAIN}_{entry_id_to_use}_{image_name}"
    registry = er.async_get(hass)
    
    # Check if sensor already exists
    entity_id = registry.async_get_entity_id(
        Platform.SENSOR, DOMAIN, sensor_unique_id
    )
    
    if not entity_id:
        # Create a new sensor entity
        from .sensor import OllamaVisionImageSensor
        new_sensor = OllamaVisionImageSensor(
            hass, 
            entry_id_to_use, 
            image_name, 
            description, 
            image_url, 
            prompt
        )
        
        # Register the entity
        registry.async_get_or_create(
            Platform.SENSOR,
            DOMAIN,
            sensor_unique_id,
            suggested_object_id=f"ollama_vision_{image_name}",
            config_entry_id=entry_id_to_use,
            device_id=registry.async_get_device_id(
                DOMAIN, 
                str((DOMAIN, entry_id_to_use))
            )
        )
        
        # Set the initial state
        entity_id = f"sensor.ollama_vision_{image_name}"
    else:
        # Update existing sensor state
        hass.states.async_set(entity_id, description, {
            "friendly_name": f"Ollama Vision {image_name}",
            "icon": "mdi:image-search",
            "image_url": image_url,
            "prompt": prompt,
            "integration_id": entry_id_to_use
        })
    
    # Store sensor info
    hass.data[DOMAIN][entry_id_to_use]["sensors"][image_name] = {
        "description": description,
        "entity_id": entity_id
    }
    
    # Fire event
    hass.bus.async_fire(
        EVENT_IMAGE_ANALYZED, 
        {
            "image_name": image_name,
            "description": description,
            "image_url": image_url,
            "integration_id": entry_id_to_use
        }
    )


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
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
