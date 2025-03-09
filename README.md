# Ollama Vision

This integration enables you to describe images with a local Ollama server with a vision enabled LLM. Optionally, you can also ask a specialized LLM to generate a more elaborate text than what the vision enabled LLM is capable of. For example enabling localization og roasting.

This is perfect if you use Frigate - you can now have a fully local LLM describing any images detected by Frigate and send the descriptions to your phone or whatever use case you may have.

The requirements are as follows:

 - The images must be available over http/https for your Home Assistant server.
 - You must have access to a Vision enabled model running on an Ollama server
 - Optionally, you must have access to a general purpose LLM running on an Ollama server for improved texts

## Features

 - Connect to one or more Ollama servers with vision-capable models
 - Analyze images with customizable prompts
 - Optionally enhance descriptions with a specialized text model
 - Create sensors with the latest image descriptions
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
 - **Vision Host**: The hostname or IP of your Ollama server with a vision model available
 - **Vision Port**: The port of your Ollama server (default: 11434)
 - **Vision Model**: The vision-capable model to use (default: moondream)
 - **Vision Model Keep-Alive**: Keep the model loaded in memory (-1 for indefinite)
 - **Enable Text Model**: Enable an LLM better suited for enhancing textual descriptions
 - **Text Model Host**: The hostname or IP of your optional text model Ollama server
 - **Text Model Port**: The port of your text model Ollama server (default: 11434)
 - **Text Model**: The text model to use (default: llama3.1)
 - **Text Model Keep-Alive**: Keep the text model loaded in memory (-1 for indefinite)

After entering the details, click "Submit" to save the configuration.

You can create multiple configurations like this with different models and model combinations if you wish. Each configuration will appear as a device with it's own sensors.

## Usage

You can queue images for description using the ollama_vision.analyze_image service. Here's an example automation that describes a person detected by Frigate:

```
alias: Describe the person outside
description: ""
triggers:
  - topic: frigate/events
    trigger: mqtt
conditions:
  - condition: template
    value_template: "{{ trigger.payload_json['after']['label'] == 'person' }}"
  - condition: template
    value_template: |-
      {{ 'front' in trigger.payload_json['after']['entered_zones'] or
         'back' in trigger.payload_json['after']['entered_zones'] }}
  - condition: template
    value_template: >-
      {% set last =
      state_attr('automation.describe_the_person_outside','last_triggered') %} {{
      last is none or (now() - last).total_seconds() > 60 }}
actions:
  - data:
      image_url: >-
        http://<HOME-ASSISTANT-IP>:8123/api/frigate/notifications/
        {{trigger.payload_json['after']['id']}}/thumbnail.jpg
      image_name: person_outside
      use_text_model: true
      text_prompt: >-
        You are an AI that introduces people that come visit me. You are
        cheeky and love a good roast. based on the following description:
        <description>{description}</description> - introduce this guest for
        me. Make it short and concise.
      device_id: <ENTER VISUAL MODE TO SELECT DEVICE>
    action: ollama_vision.analyze_image
```

This will either create or update a sensor called sensor.ollama_vision_<integration_confguration_name>_person_outside with the image description from your LLMs.

### Service Parameters

 - **Image URL** (required): URL of the image to analyze.
 - **Vision Prompt** (optional): Prompt to send to the vision model (default: "This image is from a security camera above my front door. If there are people in the image, describe thir genders, estimated ages, facial expressions (moods), hairstyles, notable facial features, and clothing styles clearly and concisely. If no people are present, describe what is on my porch clearly and concisely.").
 - **Image Name** (required): Unique name for this image (used for sensor naming).
 - **Configuration** (optional): ID of the specific Ollama Vision device to use (used for sensor naming and model selection).
 - **Use Text Model** (optional): Whether to use a specialized text model to elaborate on the vision model's description (default: false).
 - **Text Prompt** (optional): Prompt template for the text model. Use {description} to reference the vision model's output (default: "You are an AI that introduces people who come to visit me. You are cheeky and love a roast. Based on the following description: <description>{description}</description> – introduce this guest to me. Keep it short and concise, in English.")

### Events

The integration fires an event ollama_vision_image_analyzed when an image is analyzed, containing:

 - "integration_id": The device or configuration entry used.
 - "image_name": The image name given.
 - "image_url": The Image url given.
 - "prompt": The prompt given to the vision model.
 - "description": The description given by the vision model.
 - "used_text_model": True/False if a text model was employed.
 - "text_prompt": The prompt given to the specialized text model.
 - "final_description": The final description offered by the Ollama Vision integration.


You can use this event to trigger other automations for example send you a message on your phone:

```
alias: Send analysis results to my phone
triggers:
  - event_type: ollama_vision_image_analyzed
    trigger: event
conditions: []
actions:
  - continue_on_error: true
    data:
      message: |
        {{ trigger.event.data.final_description }}
      data:
        ttl: 0
        priority: high
    action: notify.mobile_app_myphone
```