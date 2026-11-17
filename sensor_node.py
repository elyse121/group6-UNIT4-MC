"""Mini Project 4.3 - generic simulated sensor publisher (run one process per sensor).

Publishes to plant1/<line>/<measure> at QoS 1 every --interval seconds. Every reading is
published with retain=True so a late-joining subscriber immediately gets the last known
value. With --lwt the node registers a Last Will on plant1/<line>/status ("offline",
QoS 1, retained) and announces "online" (retained) after connecting.

Examples:
    python3 sensor_node.py --line lineA --measure temperature --lo 60 --hi 95 --interval 2 --lwt
    python3 sensor_node.py --line lineA --measure vibration   --lo 1  --hi 10 --interval 3
    python3 sensor_node.py --line lineB --measure temperature --lo 55 --hi 90 --interval 4
"""
import argparse
import random
import signal
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt


def ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--plant", default="plant1")
    ap.add_argument("--line", required=True)
    ap.add_argument("--measure", required=True)
    ap.add_argument("--lo", type=float, required=True)
    ap.add_argument("--hi", type=float, required=True)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--lwt", action="store_true", help="register a Last Will on <plant>/<line>/status")
    ap.add_argument("--keepalive", type=int, default=5)
    args = ap.parse_args()

    topic = f"{args.plant}/{args.line}/{args.measure}"
    status_topic = f"{args.plant}/{args.line}/status"
    cid = f"{args.line}-{args.measure}"
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid)
    if args.lwt:
        c.will_set(status_topic, "offline", qos=1, retain=True)   # set BEFORE connect
    c.connect(args.host, args.port, keepalive=args.keepalive)
    c.loop_start()
    if args.lwt:
        c.publish(status_topic, "online", qos=1, retain=True).wait_for_publish()
        print(f"[{ts()}] {cid}: LWT registered, status=online (retained)", flush=True)

    def clean(*_):
        c.disconnect()
        c.loop_stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, clean)
    signal.signal(signal.SIGTERM, clean)

    while True:
        v = round(random.uniform(args.lo, args.hi), 2)
        c.publish(topic, str(v), qos=1, retain=True).wait_for_publish()
        print(f"[{ts()}] {cid}: {topic} = {v}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
