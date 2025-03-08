"""Sensor platform for Ollama Vision."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_OLLAMA_HOST, CONF_OLLAMA_MODEL
from .coordinator import OllamaVisionDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ollama Vision sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Add a status sensor
    async_add_entities([
        OllamaVisionStatusSensor(coordinator, entry.entry_id)
    ])

    # We'll dynamically add sensors as descriptions are generated
    # This is handled in the coordinator

class OllamaVisionStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing the Ollama Vision integration status."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:eye"

    def __init__(self, coordinator: OllamaVisionDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_status"
        self._attr_name = "Status"
        
    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return "Connected"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "host": self.coordinator.ollama_host,
            "model": self.coordinator.ollama_model,
            "descriptions_count": len(self.coordinator.descriptions),
        }