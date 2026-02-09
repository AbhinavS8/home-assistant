from celery import Celery
import requests
import logging

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

@app.task(bind=True)
def call_llm(self, topic: str, command: str): #topic - where command was received, command - voice command
    pass

@app.task(bind=True)
def execute_action(self, topics: list[str], payloads: list[str]):
    pass
