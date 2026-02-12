import paho.mqtt.client as mqtt
import logging
import json

BROKER_HOST = "localhost"
BROKER_PORT = 1883

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(
            client_id="home-asst-backend",
            clean_session=True  #if true, the broker doesn't remember anything about you after disconnecting
        )

        self.client.on_connect = self.on_client_connect
        self.client.on_message = self.on_client_message
        self.client.on_disconnect = self.on_client_disconnect

    #callbacks
    def on_client_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT (rc={rc})")

        # client.subscribe("home/+/events", qos=1)
        # client.subscribe("home/+/state", qos=1)

    def on_client_disconnect(self, client, userdata, rc):
        logger.warning("Disconnected from MQTT")

    def on_client_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        logger.info(f"MQTT {topic} -> {payload}")

        # enqueue to Redis / worker instead
        if topic.endswith("/command"):
            self.handle_event(topic, payload)
        else:
            self.update_db(topic,payload)


    #lifecycle
    def start(self):
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        self.client.loop_start()   # background thread

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    
    def publish(self, topic: str, payload: dict | str):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self.client.publish(topic, payload, qos=1)

    #will add later
    def handle_event(self, topic, payload):
        
        pass

    def update_payload(self,topic,payload):
        pass