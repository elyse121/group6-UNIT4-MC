# Mobile Communications Mini Projects 4.1-4.3

Setup: pip install paho-mqtt numpy   (broker: Mosquitto, or `python3 broker.py` for the pure-Python amqtt broker used here: pip install amqtt)

## 4.1 Part A  (start broker, then in separate terminals)
python3 dashboard_subscriber.py
python3 alert_subscriber.py            # --topic "factory/line3/+" for Lab Task 1
python3 sensor_publisher.py            # kill -9 it to trigger the LWT; Ctrl-C does not
Log: part_a_demo_log.txt
## 4.1 Part B
python3 link_budget_compare.py [--include-redcap] [--sensitivity]
Output: part_b_output.txt
## 4.2
python3 iot_selector.py --all --markdown results_table.md     # or --interactive
## 4.3
python3 aggregator.py
python3 sensor_node.py --line lineA --measure temperature --lo 60 --hi 95 --interval 2 --lwt
python3 sensor_node.py --line lineA --measure vibration --lo 1 --hi 10 --interval 3
python3 sensor_node.py --line lineB --measure temperature --lo 55 --hi 90 --interval 4
python3 late_joiner.py                 # retained-message demo
Log: part43_sample_log.txt   Report: report_4_3.md
