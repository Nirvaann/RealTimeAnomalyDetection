import json
import os
import time
import socket
from kafka import KafkaConsumer

def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Kafka is available!")
                return
        except OSError:
            if time.time() - start > timeout:
                raise TimeoutError("Timed out waiting for Kafka.")
            print("Waiting for Kafka...")
            time.sleep(2)

wait_for_kafka()


with open('config/config.json') as f:
    config = json.load(f)

BLACKLIST_IPS = set(config.get("blacklisted_ips", []))
THRESHOLD = config.get("anomaly_score_threshold", 0.05)

def log_alert(packet):
    with open('alerts.json', 'a') as f:
        f.write(json.dumps(packet) + '\n')

consumer = KafkaConsumer(
    'anomaly_scores',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',  # Start from the beginning if no offset
    group_id='responder-group'     # Unique group id for offset management
)


max_messages = 10  # Set to the number you want to process
count = 0

for msg in consumer:
    packet = msg.value
    ip = packet['src_ip']
    score = packet['anomaly_score']

    if ip in BLACKLIST_IPS:
        print(f"[BLOCKED] Blacklisted IP: {ip}")
        os.system(f"iptables -A INPUT -s {ip} -j DROP")
        log_alert(packet)

    elif score > THRESHOLD:
        print(f"[ALERT] High Anomaly Score {score:.4f} from {ip}")
        os.system(f"iptables -A INPUT -s {ip} -j DROP")
        log_alert(packet)

    count += 1
    if count >= max_messages:
        break
