"""Data coordinator for Ollama Vision integration."""
from __future__ import annotations

import base64
import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class OllamaVisionDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        logger: logging.Logger, 
        name: str,
        ollama_host: str,
        ollama_model: str,
        session: ClientSession,
    ) -> None:
        """Initialize."""
        super().__init__(hass, logger, name=name)
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.session = session
        self.descriptions = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        # This integration doesn't need regular polling, but we need a coordinator
        # to manage the data properly
        return self.descriptions

    async def process_image(self, image_url: str, prompt: str, image_name: str) -> None:
        """Process an image and update data."""
        try:
            # Download the image
            async with self.session.get(image_url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to download image: {response.status}")
                    return
                image_bytes = await response.read()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

            # Prepare the payload
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "images": [base64_image],
            }

            # Send to Ollama
            async with self.session.post(f"{self.ollama_host}/api/generate", json=payload) as res:
                if res.status != 200:
                    self.logger.error(f"Ollama response error: {res.status}")
                    return
                data = await res.json()
                description = data.get("response", "").strip()

                # Update our data
                safe_name = image_name.lower().replace(' ', '_')
                self.descriptions[safe_name] = description
                
                # Create/update sensor state
                self.hass.states.async_set(f"{self.name.split('_')[0]}.{safe_name}", description)

                # Fire event with results
                self.hass.bus.async_fire(f"{self.name.split('_')[0]}_image_description_generated", {
                    "image_name": image_name,
                    "description": description,
                })
                
                # Notify listeners
                self.async_set_updated_data(self.descriptions)

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")