from fastapi import FastAPI
from mqtt.client import MQTTService
from contextlib import asynccontextmanager

app = FastAPI()

#start and stop MQTT connection with server
async def lifespan(app: FastAPI):
    MQTTService.start()
    yield
    MQTTService.stop()

@app.get("/")
async def root():
    return {"message":"hello world"}