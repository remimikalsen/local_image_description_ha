"""API client for Ollama Vision."""
import logging
import aiohttp
import base64
import json
from typing import Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)

class OllamaClient:
    """Ollama API client."""

    def __init__(self, host, port, model, text_host=None, text_port=None, text_model=None):
        """Initialize the client."""
        self.host = host
        self.port = port
        self.model = model
        self.api_base_url = f"http://{host}:{port}/api"
        
        self.text_enabled = text_host is not None
        self.text_host = text_host
        self.text_port = text_port
        self.text_model = text_model
        self.text_api_base_url = f"http://{text_host}:{text_port}/api" if self.text_enabled else None

    async def analyze_image(self, image_url, prompt):
        """Send an image analysis request to Ollama."""
        try:
            # First, download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to fetch image from URL: %s", image_url)
                        return None
                    
                    image_data = await response.read()
                    
                    # Convert image to base64
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # Create the request payload
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False
                    }
                    
                    # Send the request to Ollama generate endpoint
                    async with session.post(f"{self.api_base_url}/generate", json=payload) as gen_response:
                        if gen_response.status != 200:
                            _LOGGER.error(
                                "Failed to get response from Ollama: %s", 
                                await gen_response.text()
                            )
                            return None
                        
                        result = await gen_response.json()
                        return result.get("response")
                        
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Error analyzing image: %s", exc)
            return None
            
    async def elaborate_text(self, text, prompt_template):
        """Send a text elaboration request to Ollama."""
        if not self.text_enabled:
            return text
            
        try:
            # Create the prompt by replacing {description} with the vision model output
            prompt = prompt_template.replace("{description}", text)
            
            # Create the request payload
            payload = {
                "model": self.text_model,
                "prompt": prompt,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.text_api_base_url}/generate", json=payload) as gen_response:
                    if gen_response.status != 200:
                        _LOGGER.error(
                            "Failed to get response from text Ollama: %s", 
                            await gen_response.text()
                        )
                        return text
                    
                    result = await gen_response.json()
                    return result.get("response", text)
                    
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Error elaborating text: %s", exc)
            return text
