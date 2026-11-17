"""Mini Project 4.3 - late-joining subscriber used to demonstrate retained messages.

Subscribes to plant1/+/+ for --seconds seconds and prints what arrives; messages
delivered straight from the broker's retained store are flagged RETAINED.
"""
import argparse
import time
from datetime import datetime

import paho.mqtt.client as mqtt


def ts():
    return datetime.now().strftime("%H:%M:%S")


ap = argparse.ArgumentParser()
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=1883)
ap.add_argument("--seconds", type=float, default=3.0)
args = ap.parse_args()

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="late-joiner")
c.on_connect = lambda cl, u, f, rc, p: (print(f"[{ts()}] LATE-JOINER connected, subscribing plant1/+/+", flush=True),
                                         cl.subscribe("plant1/+/+", qos=1))
c.on_message = lambda cl, u, m: print(
    f"[{ts()}] LATE-JOINER {m.topic} = {m.payload.decode()}{' (RETAINED)' if m.retain else ''}", flush=True)
c.connect(args.host, args.port, keepalive=30)
c.loop_start()
time.sleep(args.seconds)
c.loop_stop()
