"""Sensor platform for Ollama Vision."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_TEXT_MODEL_ENABLED,
    CONF_TEXT_HOST,
    CONF_TEXT_PORT,
    CONF_TEXT_MODEL,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ollama Vision sensors."""
    entities = [OllamaVisionInfoSensor(hass, entry)]

    if entry.data.get(CONF_TEXT_MODEL_ENABLED, False):
        entities.append(OllamaTextModelInfoSensor(hass, entry))

    async_add_entities(entities, True)

    @callback
    def async_create_sensor_from_event(event):
        entry_id = event.data.get("entry_id")
        image_name = event.data.get("image_name")

        sensor = OllamaVisionImageSensor(hass, entry.entry_id, image_name)
        async_add_entities([sensor], True)

    hass.bus.async_listen(f"{DOMAIN}_create_sensor", async_create_sensor_from_event)


class OllamaVisionInfoSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        config = hass.data[DOMAIN][entry.entry_id]["config"]

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_info"
        self._attr_name = f"Ollama Vision {entry.data.get('name')} Info"
        self._attr_icon = "mdi:information-outline"
        self._attr_native_value = f"{config['model']} @ {config['host']}"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]["device_info"]


class OllamaTextModelInfoSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        config = hass.data[DOMAIN][entry.entry_id]["config"]
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_text_info"
        self._attr_name = f"Ollama Text {config['name']} Info"
        self._attr_icon = "mdi:text-box-outline"
        self._attr_native_value = f"{config[CONF_TEXT_MODEL]} @ {config[CONF_TEXT_HOST]}"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]["device_info"]


class OllamaVisionImageSensor(SensorEntity):
    def __init__(self, hass, entry_id, image_name):
        self.hass = hass
        self.entry_id = entry_id
        self.image_name = image_name
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{image_name}"
        self._attr_name = f"Ollama Vision {image_name}"
        self._attr_icon = "mdi:image-search"

    async def async_update(self):
        sensor_data = self.hass.data[DOMAIN]["pending_sensors"].get(self.entry_id, {}).get(self.image_name, {})
        if sensor_data:
            description = sensor_data.get("description")
            self._attr_native_value = description[:255] if description else None

            attributes = {
                "image_url": sensor_data.get("image_url"),
                "prompt": sensor_data.get("prompt"),
                "integration_id": self.entry_id,
            }

            if sensor_data.get("used_text_model"):
                attributes.update({
                    "text_description": sensor_data.get("text_description"),
                    "text_prompt": sensor_data.get("text_prompt"),
                    "used_text_model": True
                })

            self._attr_extra_state_attributes = attributes

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry_id]["device_info"]
