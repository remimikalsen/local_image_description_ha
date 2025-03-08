"""Sensor platform for Ollama Vision."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, CONF_OLLAMA_HOST, CONF_OLLAMA_MODEL

async def async_setup_entry(
    hass: HomeAssistant, 
    config_entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Ollama Vision sensor."""
    ollama_host = config_entry.data[CONF_OLLAMA_HOST]
    ollama_model = config_entry.data[CONF_OLLAMA_MODEL]
    
    # Add a status sensor
    async_add_entities([OllamaVisionStatusSensor(config_entry.entry_id, ollama_host, ollama_model)])

class OllamaVisionStatusSensor(SensorEntity):
    """Sensor representing the Ollama Vision integration status."""

    def __init__(self, entry_id, host, model):
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._host = host
        self._model = model
        self._attr_name = f"Ollama Vision Status"
        self._attr_unique_id = f"{entry_id}_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:eye"
        
    @property
    def state(self):
        """Return the state of the sensor."""
        return "Connected"
    
    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "host": self._host,
            "model": self._model,
        }