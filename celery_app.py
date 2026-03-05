from celery import Celery
import logging
import json
import os
from openai import OpenAI
from cache import get_device_states,set_device_state

client = OpenAI()
logger = logging.getLogger(__name__)

# Load device topics from JSON
with open(os.path.join(os.path.dirname(__file__), "db/device_topics.json"), "r") as f:
    DEVICE_TOPICS = json.load(f)

app = Celery("home_assistant",
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json', #how celery serializes before passing to redis queue
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Task routing
    task_routes={
        "tasks.call_llm": {"queue": "inference"},
        "tasks.execute_action": {"queue": "actions"}
    }
)



@app.task(bind=True)
def call_llm(self, topic: str, command: str): #topic - where command was received, command - voice command
    """Analyze with ChatGPT API"""

    try:
        try:
            data = get_device_states()
        except Exception as exc:
            logger.error(f"failed to read device states {exc}")
            data=""
        response = client.responses.create(
            prompt={
                "id": "pmpt_69a2f7e5dc3881908eb7903be7f121c002c22c5bc2df80f6",
                "version": "4"
            },
            input= data+"\n\n"+command
        )   
        for item in response.output:

            for content in item.content:
                if content.type == "output_text":
                    # Parse the JSON string
                    data = json.loads(content.text)
                    
                    # Extract intent
                    intent = data["intent_format"]
                    function_name = intent["name"]        # "TurnOff"
                    arguments = intent["arguments"]       # {"name": "fan.kitchen_fan"}
                    
                    print(f"Function: {function_name}")
                    print(f"Arguments: {arguments}")
                    
                    # Extract state if needed
                    state = data.get("state_schema", {})
                    print(f"State: {state}")
                
                    execute_action.delay(
                        function_name=function_name,
                        arguments=arguments
                    )
        
    except Exception as exc:
        logger.error(f"LLM analysis failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True)
def execute_action(self, function_name, arguments, priority=0):

    entity_name = arguments.get("name")
    device = DEVICE_TOPICS.get(entity_name) #NEED TO fill, using JSON for now

    if not device:
        logger.warning(f"No MQTT topic configured for {entity_name}")
        return

    topic = device["topic"]

    payload = {}

    if function_name == "TurnOn":
        payload = {"state": "ON"}

    elif function_name == "TurnOff":
        payload = {"state": "OFF"}

    elif function_name == "LightSet":
        payload = {"state": "ON"}

        if arguments.get("brightness") is not None:
            payload["brightness"] = arguments["brightness"]

        if arguments.get("color") is not None:
            payload["color"] = arguments["color"]

    else:
        logger.warning(f"Unknown function: {function_name}")
        return

    # Publish directly using paho-mqtt (avoids circular import, and the service class is stupid anyways)
    import paho.mqtt.publish as publish
    publish.single(
        topic,
        payload=json.dumps(payload),
        hostname="localhost",
        port=1883,
        qos=1
    )
    logger.info(f"Published to {topic}: {payload}")
    set_device_state(device, payload) 