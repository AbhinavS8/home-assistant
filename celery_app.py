from celery import Celery
import requests
import logging
import json

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
    """Analyze with ChatGPT API"""
    try:
        prompt = """e
        """
      
        response = requests.post(
              "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=30
        )

        if response.status_code ==200:
            result = response.json()
            analysis = json.loads(result)
            for action in analysis.get("actions", []):
                execute_action.delay(action, analysis.get("priority",0))
                
        else:
            logger.error(f"OpenAI API error: {response.status_code}")
    except Exception as exc:
        logger.error(f"LLM analysis failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))



@app.task(bind=True)
def execute_action(self, command, priority): #list of dicts (topics: payloads) to execute
    #maybe use pydantic in future?
    pass
