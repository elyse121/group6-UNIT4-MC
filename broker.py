"""Local MQTT broker (amqtt) used in place of Mosquitto for the lab demo."""
import asyncio, logging
from amqtt.broker import Broker

CONFIG = {
    "listeners": {"default": {"type": "tcp", "bind": "127.0.0.1:1883"}},
    "sys_interval": 0,
    "auth": {"allow-anonymous": True, "plugins": ["auth_anonymous"]},
    "topic-check": {"enabled": False},
}

async def main():
    logging.basicConfig(level=logging.WARNING)
    b = Broker(CONFIG)
    await b.start()
    print("broker up on 127.0.0.1:1883", flush=True)
    await asyncio.Event().wait()

asyncio.run(main())
