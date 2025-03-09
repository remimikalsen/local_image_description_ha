"""Sensor platform for Ollama Vision."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_TEXT_MODEL_ENABLED, CONF_TEXT_MODEL_ENABLED, CONF_TEXT_MODEL_ENABLED, CONF_TEXT_HOST, CONF_TEXT_PORT, CONF_TEXT_MODEL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ollama Vision sensors."""
    # Create the info sensor for this configuration entry
    info_sensor = OllamaVisionInfoSensor(hass, entry)
    entities = [vision_info_sensor]
    
    # Create text model info sensor if text model is enabled
    text_model_enabled = entry.data.get(CONF_TEXT_MODEL_ENABLED) or entry.options.get(CONF_TEXT_MODEL_ENABLED, False)
    if text_model_enabled:
        text_info_sensor = OllamaTextModelInfoSensor(hass, entry)
        entities.append(text_info_sensor)
    
    async_add_entities(entities, True)
    
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

class OllamaTextModelInfoSensor(SensorEntity):
    """Sensor showing information about the Ollama Text Model."""

    def __init__(self, hass, entry):
        """Initialize the sensor."""
        self.hass = hass
        self.entry = entry
        self.entry_id = entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_text_info"
        self._attr_name = f"Ollama Text {entry.data.get('name')} Info"
        self._attr_icon = "mdi:text-box-outline"
        
        # Get device info from hass.data
        self._device_info = hass.data[DOMAIN][entry.entry_id]["device_info"]
        
        # Set initial state - use model name and host
        text_host = hass.data[DOMAIN][entry.entry_id]["config"].get(CONF_TEXT_HOST)
        text_model = hass.data[DOMAIN][entry.entry_id]["config"].get(CONF_TEXT_MODEL)
        self._attr_native_value = f"{text_model} @ {text_host}"
        
        # Store attributes
        self._attr_extra_state_attributes = {
            "integration_id": entry.entry_id,
            "host": text_host,
            "port": hass.data[DOMAIN][entry.entry_id]["config"].get(CONF_TEXT_PORT),
            "model": text_model,
            "friendly_name": f"Text Model for {entry.data.get('name')}"
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
        
        # Get sensor data from pending_sensors
        sensor_data = hass.data[DOMAIN].get("pending_sensors", {}).get(entry_id, {}).get(image_name, {})
        
        # Set state (vision description) - truncate if needed
        self._attr_native_value = description[:255] if len(description) > 255 else description
        
        # Set attributes
        self._attr_extra_state_attributes = {
            "image_url": image_url,
            "prompt": prompt,
            "integration_id": entry_id
        }
        
        # Add text model attributes if available
        if "text_description" in sensor_data:
            self._attr_extra_state_attributes["text_description"] = sensor_data["text_description"]
        
        if "text_prompt" in sensor_data:
            self._attr_extra_state_attributes["text_prompt"] = sensor_data["text_prompt"]
            
        if "used_text_model" in sensor_data:
            self._attr_extra_state_attributes["used_text_model"] = sensor_data["used_text_model"]
        
        # Get device info from hass.data
        self._device_info = hass.data[DOMAIN][entry_id]["device_info"]

    @property
    def device_info(self):
        """Return device information about this entity."""
        return self._device_info
