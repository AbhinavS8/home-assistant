from celery import Celery
import requests
import logging
import json
import os
from openai import OpenAI

client = OpenAI()
logger = logging.Logger(__name__)

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


# response = client.responses.create(
#   prompt={
#     "id": "pmpt_69a2f7e5dc3881908eb7903be7f121c002c22c5bc2df80f6",
#     "version": "2"
#   }
# )

@app.task(bind=True)
def call_llm(self, topic: str, command: str): #topic - where command was received, command - voice command
    """Analyze with ChatGPT API"""
    try:
        response = client.responses.create(
            prompt={
                "id": "pmpt_69a2f7e5dc3881908eb7903be7f121c002c22c5bc2df80f6",
                "version": "3"
            },
            input= {"role": "user", "content": command}
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
def execute_action(self, function_name, arguments, priority=0): #payload response
    #maybe use pydantic in future?
    pass
