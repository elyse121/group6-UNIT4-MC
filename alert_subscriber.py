"""Mini Project 4.1, Part A - alert subscriber.

Subscribes to the wildcard topic factory/+/temperature (default) at QoS 1 and
prints an ALERT line only when a value exceeds the threshold (default 90.0).

Lab Task 1: run with --topic "factory/line3/+" to also receive humidity; the
threshold logic is applied only to topics ending in /temperature.
"""
import argparse
from datetime import datetime

import paho.mqtt.client as mqtt

THRESHOLD = 90.0


def ts():
    return datetime.now().strftime("%H:%M:%S")


def make_handlers(topic, threshold):
    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"[{ts()}] ALERTER connected ({reason_code}); subscribing to {topic}", flush=True)
        client.subscribe(topic, qos=1)

    def on_message(client, userdata, msg):
        if not msg.topic.endswith("/temperature"):
            return
        try:
            value = float(msg.payload.decode())
        except ValueError:
            return
        if value > threshold:
            print(f"[{ts()}] ALERT {msg.topic} = {value} exceeds {threshold}", flush=True)

    return on_connect, on_message


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--topic", default="factory/+/temperature")
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="alerter")
    c.on_connect, c.on_message = make_handlers(args.topic, args.threshold)
    c.connect(args.host, args.port, keepalive=30)
    c.loop_forever()


if __name__ == "__main__":
    main()
