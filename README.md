# Home Assistant

LLM-integrated MQTT device controller that uses natural language to control smart home devices.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MQTT Broker   │────▶│   MQTT Client   │────▶│   Redis Queue   │
│   (Mosquitto)   │     │   (main.py)     │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Smart Devices  │◀────│ Celery Workers  │◀────│   OpenAI API    │
│  (via MQTT)     │     │ (execute_action)│     │   (call_llm)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## How It Works

1. **Voice commands** are published to MQTT topics (e.g., `home/mic1/command`)
2. **MQTT Client** receives commands and queues them to Redis via Celery
3. **LLM Worker** sends commands to OpenAI to parse intent (e.g., "turn on kitchen light" → `TurnOn`, `light.kitchen_light`)
4. **Action Worker** executes the parsed command by publishing to device MQTT topics
5. **Device state** is cached in Redis for context-aware responses

## Project Structure

```
home-assistant/
├── main.py              # Entry point - starts MQTT listener
├── celery_app.py        # Celery tasks (call_llm, execute_action)
├── cache.py             # Redis cache helpers
├── mqtt/
│   └── client.py        # MQTT service class
├── db/
│   └── device_topics.json  # Device configuration
├── mosquitto.conf       # MQTT broker config
└── requirements.txt     # Python dependencies
```

## Prerequisites

- Python 3.10+
- Redis server
- Mosquitto MQTT broker
- OpenAI API key

## Installation

### 1. Clone and setup virtual environment

```bash
git clone https://github.com/AbhinavS8/home-assistant.git
cd home-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file or export directly:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Configure devices

Edit `db/device_topics.json` to add your devices:

```json
{
  "light.kitchen_light": {
    "topic": "home/kitchen/light/set",
    "name": "Kitchen Light",
    "type": "light"
  }
}
```

## Running the Application

Start each service in a separate terminal:

### Terminal 1: Redis
```bash
redis-server
```

### Terminal 2: Mosquitto MQTT Broker
```bash
mosquitto -c mosquitto.conf
```

### Terminal 3: Celery Worker
```bash
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

### Terminal 4: Main Application
```bash
source venv/bin/activate
python main.py
```

## Testing

Send a test command via MQTT:

```bash
mosquitto_pub -h localhost -t "home/mic1/command" -m "turn on the kitchen light"
```

Subscribe to device topics to see output:

```bash
mosquitto_sub -h localhost -t "home/#" -v
```

## Supported Commands

| Command Type | Example | Intent |
|--------------|---------|--------|
| Turn On | "turn on the kitchen light" | `TurnOn` |
| Turn Off | "turn off the bedroom fan" | `TurnOff` |
| Set Light | "set living room light to 50%" | `LightSet` |

## Configuration

### MQTT Broker (mosquitto.conf)

```
listener 1883
allow_anonymous true
```

### Redis Databases

| DB | Usage |
|----|-------|
| 0 | Celery task queue |
| 1 | Device state cache |

## Adding New Devices

1. Add device to `db/device_topics.json`
2. Ensure device subscribes to its MQTT topic (e.g., `home/kitchen/light/set`)
3. Device should accept JSON payloads: `{"state": "ON"}`, `{"state": "OFF", "brightness": 50}`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No API request made | Ensure Celery worker is running |
| Module not found | Activate venv before running |
| MQTT not connecting | Check Mosquitto is running on port 1883 |
| Redis connection refused | Start Redis server |

## License

MIT
