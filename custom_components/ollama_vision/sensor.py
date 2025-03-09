"""Sensor platform for Ollama Vision."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ollama Vision sensors."""
    # Create the info sensor for this configuration entry
    info_sensor = OllamaVisionInfoSensor(hass, entry)
    async_add_entities([info_sensor], True)
    
    # Create a listener for new sensor requests
    @callback
    def async_create_sensor_from_event(event):
        """Create a sensor entity from an event."""
        entry_id = event.data.get("entry_id")
        image_name = event.data.get("image_name")
        
        if (entry_id == entry.entry_id and 
            entry_id in hass.data[DOMAIN].get("pending_sensors", {}) and
            image_name in hass.data[DOMAIN]["pending_sensors"][entry_id]):
            
            sensor_data = hass.data[DOMAIN]["pending_sensors"][entry_id][image_name]
            
            # Create the sensor entity
            sensor = OllamaVisionImageSensor(
                hass,
                entry_id,
                image_name,
                sensor_data["description"],
                sensor_data["image_url"],
                sensor_data["prompt"]
            )
            
            # Add it to Home Assistant
            async_add_entities([sensor], True)
    
    # Register the event listener
    hass.bus.async_listen(f"{DOMAIN}_create_sensor", async_create_sensor_from_event)

class OllamaVisionInfoSensor(SensorEntity):
    """Sensor showing information about the Ollama Vision integration."""

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_info"
        self._attr_name = f"Ollama Vision {entry.data.get('name')} Info"
        self._attr_icon = "mdi:information-outline"
        
        # Get device info from hass.data
        self._device_info = hass.data[DOMAIN][entry.entry_id]["device_info"]
        
        # Set initial state - use model name instead of entry_id
        host = hass.data[DOMAIN][entry.entry_id]["config"]["host"]
        model = hass.data[DOMAIN][entry.entry_id]["config"]["model"]
        self._attr_native_value = f"{model} @ {host}"
        
        # Store entry_id in attributes but not as the main value
        self._attr_extra_state_attributes = {
            "integration_id": entry.entry_id,
            "host": hass.data[DOMAIN][entry.entry_id]["config"]["host"],
            "port": hass.data[DOMAIN][entry.entry_id]["config"]["port"],
            "model": hass.data[DOMAIN][entry.entry_id]["config"]["model"],
            "friendly_name": hass.data[DOMAIN][entry.entry_id]["config"]["name"]
        }

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._device_info

class OllamaVisionImageSensor(SensorEntity):
    """Sensor for Ollama Vision image analysis results."""

    def __init__(self, hass, entry_id, image_name, description, image_url, prompt):
        """Initialize the sensor."""
        self.hass = hass
        self.entry_id = entry_id
        self.image_name = image_name
        
        # Set unique ID and name
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{image_name}"
        self._attr_name = f"Ollama Vision {image_name}"
        self._attr_icon = "mdi:image-search"
        
        # Set state and attributes
        self._attr_native_value = description
        self._attr_extra_state_attributes = {
            "image_url": image_url,
            "prompt": prompt,
            "integration_id": entry_id
        }
        
        # Get device info from hass.data
        self._device_info = hass.data[DOMAIN][entry_id]["device_info"]

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._device_info
