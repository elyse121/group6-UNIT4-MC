"""Mini Project 4.1, Part A - operator dashboard subscriber.

Subscribes to factory/line3/temperature and factory/line3/status at QoS 1 and
prints a timestamped line per event. Retained messages are flagged so the
late-joiner behaviour is visible.
"""
import argparse
from datetime import datetime

import paho.mqtt.client as mqtt

TOPICS = [("factory/line3/temperature", 1), ("factory/line3/status", 1)]


def ts():
    return datetime.now().strftime("%H:%M:%S")


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[{ts()}] DASHBOARD connected ({reason_code}); subscribing", flush=True)
    client.subscribe(TOPICS)


def on_message(client, userdata, msg):
    tag = " (RETAINED)" if msg.retain else ""
    print(f"[{ts()}] DASHBOARD {msg.topic} = {msg.payload.decode()}{tag}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    args = ap.parse_args()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dashboard")
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(args.host, args.port, keepalive=30)
    c.loop_forever()


if __name__ == "__main__":
    main()
