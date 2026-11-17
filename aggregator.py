"""Mini Project 4.3 - aggregator / logger / alerter.

ONE wildcard subscription ("plant1/+/+", QoS 1) receives every sensor reading and status
message, however many sensors exist and whenever they appear. For each message it:
  * timestamps it and appends it to a CSV log,
  * updates the latest value per topic,
  * applies an independent per-topic threshold (exact-topic entry wins, else the
    per-measurement default) and logs an ALERT line when exceeded.
Every --summary seconds it prints the latest value per topic and the number of readings.
"""
import argparse
import csv
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt

SUBSCRIPTION = "plant1/+/+"

# Independent thresholds. Exact topics override the per-measurement defaults.
THRESHOLDS = {
    "plant1/lineA/temperature": 80.0,   # lineA runs hotter-sensitive process
    "temperature": 85.0,                # default for any other temperature topic
    "vibration": 7.0,                   # mm/s default for any vibration topic
}

latest = {}      # topic -> (timestamp, value or text)
counts = {}      # topic -> number of messages
lock = threading.Lock()


def ts():
    return datetime.now().strftime("%H:%M:%S")


def threshold_for(topic):
    return THRESHOLDS.get(topic, THRESHOLDS.get(topic.rsplit("/", 1)[-1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--csv", default="plant_log.csv")
    ap.add_argument("--summary", type=float, default=10.0)
    args = ap.parse_args()

    f = open(args.csv, "w", newline="")
    writer = csv.writer(f)
    writer.writerow(["timestamp", "topic", "value", "retained"])

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="aggregator")

    def on_connect(client, userdata, flags, rc, props):
        print(f"[{ts()}] AGG connected; single subscription {SUBSCRIPTION} (QoS 1)", flush=True)
        client.subscribe(SUBSCRIPTION, qos=1)

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        now = datetime.now().isoformat(timespec="seconds")
        with lock:
            if msg.topic not in counts:
                print(f"[{ts()}] AGG NEW TOPIC discovered: {msg.topic}", flush=True)
            counts[msg.topic] = counts.get(msg.topic, 0) + 1
            latest[msg.topic] = (now, payload)
            writer.writerow([now, msg.topic, payload, int(msg.retain)])
            f.flush()
        tag = " (RETAINED)" if msg.retain else ""
        print(f"[{ts()}] AGG {msg.topic} = {payload}{tag}", flush=True)
        limit = threshold_for(msg.topic)
        if limit is not None:
            try:
                if float(payload) > limit:
                    print(f"[{ts()}] ALERT {msg.topic} = {payload} exceeds {limit}", flush=True)
            except ValueError:
                pass
        elif msg.topic.endswith("/status"):
            print(f"[{ts()}] STATUS {msg.topic} -> {payload}", flush=True)

    c.on_connect, c.on_message = on_connect, on_message
    c.connect(args.host, args.port, keepalive=30)
    c.loop_start()

    try:
        while True:
            time.sleep(args.summary)
            with lock:
                print(f"\n[{ts()}] ---- SUMMARY (latest per topic) ----", flush=True)
                for t in sorted(latest):
                    when, v = latest[t]
                    print(f"   {t:<28}{v:>8}   n={counts[t]}", flush=True)
                print(flush=True)
    except KeyboardInterrupt:
        c.loop_stop()
        f.close()


if __name__ == "__main__":
    main()
