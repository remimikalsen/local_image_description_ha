# Ollama Vision
This is a Home Assistant integration, installable via HACS, to describe images through a local Ollama server with a vision-enabled LLM.

## Features

 - Connect to one or more Ollama servers with vision-capable models
 - Analyze images with customizable prompts
 - Optionally enhance descriptions with a text model
 - Create sensors with image descriptions
 - Trigger events when images are analyzed

## Installation

To install the "Ollama Vision" integration in Home Assistant, follow these steps:

 1. Ensure you have HACS (Home Assistant Community Store) installed.
 2. Add the repository to HACS:

    - Go to HACS
    - Click the three dots in the upper right corner
    - Select "Custom repositories"
    - Paste the repository link: https://github.com/remimikalsen/local_image_description_ha
    - Select type: Integration
    - Click "Add"

 3. Close the modal, search for "Ollama Vision" and click on it
 4. Choose "Download"

At this point, you must restart Home Assistant before you can continue.

## Configuration

Go to Home Assistant's Configuration page.

 1. Click on "Devices & Services"
 2. Click on the "+" button to add a new integration
 3. Search for "Ollama Vision" and select it

You will be prompted to enter the following details:

 - **Name**: A name for this Ollama Vision instance
 - **Host**: The hostname or IP of your Ollama server
 - **Port**: The port of your Ollama server (default: 11434)
 - **Vision Model**: The vision-capable model to use (default: moondream)
 - **Vision Model Keep-Alive**: Keep the model loaded in memory (-1 for indefinite)
 - **Enable Text Model**: Enable an LLM better suited for enhancing textual descriptions
 - **Text Model Host**: The hostname or IP of your text model Ollama server
 - **Text Model Port**: The port of your text model Ollama server (default: 11434)
 - **Text Model**: The text model to use (default: llama3.1)
 - **Text Model Keep-Alive**: Keep the text model loaded in memory (-1 for indefinite)

After entering the details, click "Submit" to save the configuration.

## Usage

You can send images for description using the ollama_vision.analyze_image service. Here's an example automation that describes a person detected by Frigate:

```
alias: Describe person at veranda
trigger:
  - topic: frigate/events
    trigger: mqtt
conditions:
  - "{{ trigger.payload_json['after']['label'] == 'person' }}"
  - "{{ 'veranda' in trigger.payload_json['after']['entered_zones'] }}"
actions:
  - service: ollama_vision.analyze_image
    data:
      image_url: "http://homeassistant.local:8123/api/frigate/notifications/{{trigger.payload_json['after']['id']}}/thumbnail.jpg"
      image_name: "veranda"
      prompt: "This image is from a security camera located above my door. Describe the gender, age, mood, hair style and the clothes of the person in this image."
      use_text_model: false
```

This will create or update a sensor called sensor.ollama_vision_veranda with the image description.

### Service Parameters

 - **image_url** (required): URL of the image to analyze
 - **image_name** (required): Unique name for this image (used for sensor naming)
 - **prompt** (optional): Prompt to send to the vision model (default: "Describe what you see in this image clearly and concisely.")
 - **device_id** (optional): ID of the specific Ollama Vision device to use
 - **use_text_model** (optional): Whether to use the text model to elaborate on the vision model's description (default: false)
 - **text_prompt** (optional): Prompt template for the text model. Use {description} to reference the vision model's output (default: "Elaborate on this image description: {description}. Make it detailed and descriptive.")

### Events

The integration fires an event ollama_vision_image_analyzed when an image is analyzed, containing:
 - image_name
 - description
 - image_url
 - integration_id
 - final_description (if text model was used)
 - used_text_model (if text model was used)

You can use this event to trigger other automations.