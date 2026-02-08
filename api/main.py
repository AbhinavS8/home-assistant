from fastapi import FastAPI
import paho.mqtt.client as mqtt

app = FastAPI()

@app.get("/")
async def root():
    return {"message":"hello world"}