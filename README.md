# Ollama Vision

This is a Home Assistant integration, installable via HACS, to describe images through a local Ollama server with a vision enabled LLM.


## Installation
To install the "Ollama Vision" integration in Home Assistant, follow these steps:

1. Ensure you have HACS (Home Assistant Community Store) installed.
2. Add the repository to HACS
  - Go to Hacs
  - Click the three dots in the upper right corner
  - Paste the repository link: https://github.com/remimikalsen/local_image_description_ha
  - Select type: Integration
  - Add
3. Close the modal, search for "Ollama Vision" and click on it
  - Choose "Download"


## Configuration

Go to Home Assistant's Configuration page.

1. Click on "Devices & Services".
2. Click on the "+" button to add a new integration.
3. Search for "Ollama Vision" and select it.

*You will be prompted to enter the following details:*
- Ollama Host: The URL of your local Ollama server (default: http://localhost:11434).
- Ollama Model: The model to use for image description (default: moondream).
- Prompt: The default prompt to use for generating descriptions (default: This image is from a security camera located above my front door. Describe the gender, age, mood, hair style and the clothes of the person in this image.).

After entering the details, click "Submit" to save the configuration.
Your integration should now be set up and ready to use. 

You can send images for description using the `ollama_vision` service, for example from an automation upon motion detection from Frigate

```
alias: Describe person at veranda
trigger:
  - topic: frigate/events
    trigger: mqtt
conditions:
  - "{{ trigger.payload_json['after']['label'] == 'person' }}"
  - "{{ 'veranda' in trigger.payload_json['after']['entered_zones'] }}"
actions:
  - service: ollama_vision.generate_image_description
    data:
      image_url: "http://homeassistant.local:8123/api/frigate/notifications/{{trigger.payload_json['after']['id']}}/thumbnail.jpg"
      camera_name: "veranda"
```

This will add an image description to:

```
ollama_vision.veranda
```

Which you can use to whatever.

