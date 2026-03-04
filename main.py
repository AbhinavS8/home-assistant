# from fastapi import FastAPI
# from mqtt.client import MQTTService
# from contextlib import asynccontextmanager

# app = FastAPI()

# #start and stop MQTT connection with server
# async def lifespan(app: FastAPI):
#     MQTTService.start()
#     yield
#     MQTTService.stop()

# @app.get("/")
# async def root():
#     return {"message":"hello world"}

# main.py

from mqtt.client import MQTTService
import signal
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    mqtt = MQTTService()
    mqtt.start()
    
    # Handle graceful shutdown
    def shutdown(sig, frame):
        print("Shutting down...")
        mqtt.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Keep running
    print("Home Assistant running. Press Ctrl+C to stop.")
    signal.pause()

if __name__ == "__main__":
    main()