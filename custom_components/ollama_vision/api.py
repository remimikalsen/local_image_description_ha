"""API client for Ollama Vision with streaming support."""
import logging
import aiohttp
import base64
import json

_LOGGER = logging.getLogger(__name__)

class OllamaClient:
    """Ollama API client with streaming support."""

    def __init__(
        self, 
        host: str, 
        port: int, 
        model: str, 
        text_host: str = None, 
        text_port: int = None, 
        text_model: str = None, 
        vision_keepalive: int = -1, 
        text_keepalive: int = -1
    ):
        """Initialize the client."""
        self.host = host
        self.port = port
        self.model = model
        self.vision_keepalive = vision_keepalive
        self.api_base_url = f"http://{host}:{port}/api"
        
        self.text_enabled = text_host is not None
        self.text_host = text_host
        self.text_port = text_port
        self.text_model = text_model
        self.text_keepalive = text_keepalive
        self.text_api_base_url = (
            f"http://{text_host}:{text_port}/api" if self.text_enabled else None
        )

    async def analyze_image(self, image_url: str, prompt: str) -> str:
        """
        Send an image analysis request to the Vision model. 
        Returns the combined string from all streamed chunks, or None if error.
        """
        try:
            # 1) Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to fetch image from URL: %s", image_url)
                        return None
                    image_data = await response.read()

            # 2) Convert image to base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # 3) Build request payload for streaming
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": True,
                "keep_alive": self.vision_keepalive
            }

            # 4) POST to Ollama /api/generate with streaming
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/generate"
                async with session.post(url, json=payload) as gen_response:
                    if gen_response.status != 200:
                        text = await gen_response.text()
                        _LOGGER.error("Failed response from Ollama: %s", text)
                        return None
                    
                    # 5) Collect partial tokens from the SSE stream
                    final_text = await self._collect_stream(gen_response)
                    return final_text

        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Error analyzing image: %s", exc)
            return None

    async def elaborate_text(self, text: str, prompt_template: str) -> str:
        """
        Send a text elaboration request to the Text model (if enabled).
        Returns the combined string from all streamed chunks, or the original text if error/disabled.
        """
        if not self.text_enabled:
            # If no text model configured, just return the original text
            return text
        
        try:
            # 1) Create the prompt by substituting {description} in the template
            prompt = prompt_template.replace("{description}", text)
            
            # 2) Build request payload for streaming
            payload = {
                "model": self.text_model,
                "prompt": prompt,
                "stream": True, 
                "keep_alive": self.text_keepalive
            }

            # 3) POST to the text model /api/generate with streaming
            async with aiohttp.ClientSession() as session:
                url = f"{self.text_api_base_url}/generate"
                async with session.post(url, json=payload) as gen_response:
                    if gen_response.status != 200:
                        text_resp = await gen_response.text()
                        _LOGGER.error("Failed response from text Ollama: %s", text_resp)
                        return text

                    # 4) Collect partial tokens from the SSE stream
                    final_text = await self._collect_stream(gen_response)
                    return final_text if final_text else text

        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error("Error elaborating text: %s", exc)
            return text

    async def _collect_stream(self, response: aiohttp.ClientResponse) -> str:
        """
        Helper method to read from the Ollama streaming response (SSE).
        Gathers all partial 'response' fields into one final string.
        """
        collected = []
        async for raw_line in response.content:
            line = raw_line.decode("utf-8").rstrip("\n")
            if not line.startswith("data: "):
                # SSE lines can include "event:" or empty lines. We skip them here.
                continue
            data_str = line[len("data: "):].strip()
            if data_str == "[DONE]":
                # The server signals end of stream
                break

            # Attempt to parse the JSON chunk
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                _LOGGER.warning("Received non-JSON data in stream: %s", data_str)
                continue

            # If it has a "response" key, it's some partial text
            chunk = data_json.get("response")
            if chunk:
                collected.append(chunk)

            # Some builds might have a "done": true flag. If so, you can break early:
            if data_json.get("done"):
                break

        return "".join(collected)
