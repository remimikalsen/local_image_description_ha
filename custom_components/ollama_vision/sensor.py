"""Sensor platform for Ollama Vision."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_TEXT_MODEL_ENABLED,
    CONF_TEXT_HOST,
    CONF_TEXT_MODEL,
    CONF_MODEL,
    CONF_HOST,
    INTEGRATION_NAME,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ollama Vision sensors."""
    entities = [OllamaVisionInfoSensor(hass, entry)]

    text_model_enabled = entry.options.get(
        CONF_TEXT_MODEL_ENABLED, 
        entry.data.get(CONF_TEXT_MODEL_ENABLED, False)
)
    if text_model_enabled:
        entities.append(OllamaTextModelInfoSensor(hass, entry))

    async_add_entities(entities, True)

    @callback
    def async_create_sensor_from_event(event):
        entry_id = event.data.get("entry_id")
        image_name = event.data.get("image_name")
        sensor_unique_id = f"{DOMAIN}_{entry_id}_{image_name}"
        
        # Initialize or get the dict to track created sensors
        created_sensors = hass.data[DOMAIN].setdefault("created_sensors", {})
        
        if sensor_unique_id in created_sensors:
            # Sensor already exists: trigger a direct update
            created_sensors[sensor_unique_id].async_schedule_update()
        else:
            # Create and register a new sensor entity
            sensor = OllamaVisionImageSensor(hass, entry_id, image_name)
            async_add_entities([sensor], True)
            created_sensors[sensor_unique_id] = sensor

    hass.bus.async_listen(f"{DOMAIN}_create_sensor", async_create_sensor_from_event)


class OllamaVisionInfoSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        config = hass.data[DOMAIN][entry.entry_id]["config"]

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_vision_info"
        self._attr_name = f"Vision model {config['name']}"
        self._attr_icon = "mdi:information-outline"
        self._attr_native_value = f"{config[CONF_MODEL]} @ {config[CONF_HOST]}"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]["device_info"]


class OllamaTextModelInfoSensor(SensorEntity):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        config = hass.data[DOMAIN][entry.entry_id]["config"]

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_text_info"
        self._attr_name = f"Text model {config['name']}"
        self._attr_icon = "mdi:information-outline"
        self._attr_native_value = f"{config[CONF_TEXT_MODEL]} @ {config[CONF_TEXT_HOST]}"

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry.entry_id]["device_info"]


class OllamaVisionImageSensor(SensorEntity):
    def __init__(self, hass, entry_id, image_name):
        self.hass = hass
        self.entry_id = entry_id
        self.image_name = image_name

        # Fetch the name of the config entry from hass.data:
        config_name = self.hass.data[DOMAIN][entry_id]["config"]["name"]
        # Slugify it so that Home Assistant’s auto-entity_id generation
        # doesn’t produce weird characters:
        config_name_slug = slugify(config_name)

        # Make the user-facing name reflect both the config_name and image_name:
        self._attr_name = f"{INTEGRATION_NAME} {config_name_slug} {image_name}"

        # Unique ID remains the same; that’s what ensures the sensor is “the same” across restarts:
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{image_name}"

        self._attr_icon = "mdi:image-search"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
    
    @callback
    def async_schedule_update(self):
        """Update the entity when new data is received."""
        sensor_data = self.hass.data[DOMAIN]["pending_sensors"].get(self.entry_id, {}).get(self.image_name, {})
        if sensor_data:
            description = sensor_data.get("description")
            self._attr_native_value = description[:255] if description else None
            attributes = {
                "integration_id": self.entry_id,
                "image_url": sensor_data.get("image_url"),
                "prompt": sensor_data.get("prompt"),                
            }
            if sensor_data.get("used_text_model"):
                attributes.update({
                    "used_text_model": True,
                    "text_prompt": sensor_data.get("text_prompt"),
                    "final_description": sensor_data.get("final_description")
                })
            self._attr_extra_state_attributes = attributes
            self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the sensor."""
        sensor_data = self.hass.data[DOMAIN]["pending_sensors"].get(self.entry_id, {}).get(self.image_name, {})
        if sensor_data:
            description = sensor_data.get("description")
            self._attr_native_value = description[:255] if description else None
            attributes = {
                "integration_id": self.entry_id,
                "image_url": sensor_data.get("image_url"),
                "prompt": sensor_data.get("prompt")                
            }
            if sensor_data.get("used_text_model"):
                attributes.update({
                    "used_text_model": True,
                    "text_prompt": sensor_data.get("text_prompt"),
                    "final_description": sensor_data.get("final_description")                    
                })
            self._attr_extra_state_attributes = attributes

    @property
    def device_info(self):
        return self.hass.data[DOMAIN][self.entry_id]["device_info"]