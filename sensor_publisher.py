"""Mini Project 4.1, Part A - sensor publisher.

Client ID "line3-temp-sensor". Registers a Last Will (offline, QoS 1, retained),
publishes "online" (retained) on connect, then every 5 s publishes a simulated
temperature (60-95) to factory/line3/temperature at QoS 1. The first reading is
retained so late subscribers see the last known value immediately.

Usage: python3 sensor_publisher.py [--host 127.0.0.1] [--port 1883] [--interval 5]
Kill it with `kill -9` (ungraceful) to trigger the LWT; Ctrl-C does a clean
disconnect, which does NOT trigger the LWT.
"""
import argparse
import random
import signal
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

TEMP_TOPIC = "factory/line3/temperature"
STATUS_TOPIC = "factory/line3/status"


def ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--keepalive", type=int, default=5,
                    help="short keep-alive so the broker detects a dead client quickly")
    args = ap.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="line3-temp-sensor")

    # Step 4: register the Last Will BEFORE connecting.
    client.will_set(STATUS_TOPIC, payload="offline", qos=1, retain=True)

    client.connect(args.host, args.port, keepalive=args.keepalive)
    client.loop_start()

    # Step 4: announce "online" (retained) immediately after connecting.
    client.publish(STATUS_TOPIC, "online", qos=1, retain=True).wait_for_publish()
    print(f"[{ts()}] connected, status=online (retained)", flush=True)

    def clean_exit(*_):
        print(f"[{ts()}] clean disconnect (LWT will NOT fire)", flush=True)
        client.publish(STATUS_TOPIC, "offline", qos=1, retain=True).wait_for_publish()
        client.disconnect()
        client.loop_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, clean_exit)
    signal.signal(signal.SIGTERM, clean_exit)

    first = True
    while True:
        value = round(random.uniform(60, 95), 1)
        # Step 5: first reading retained so a late joiner gets it immediately.
        info = client.publish(TEMP_TOPIC, str(value), qos=1, retain=first)
        info.wait_for_publish()
        print(f"[{ts()}] published {value} to {TEMP_TOPIC} (QoS 1, retain={first})", flush=True)
        first = False
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
