import json
import os
import time
import socket
from kafka import KafkaConsumer, errors, TopicPartition
import uuid

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

def create_consumer_with_retry(*args, **kwargs):
    for i in range(10):
        try:
            return KafkaConsumer(*args, **kwargs)
        except errors.NoBrokersAvailable:
            print("Kafka not ready, retrying in 5 seconds...")
            time.sleep(5)
    raise RuntimeError("Kafka not available after multiple retries.")

with open('config/config.json') as f:
    config = json.load(f)

BLACKLIST_IPS = set(config.get("blacklisted_ips", []))
THRESHOLD = config.get("anomaly_score_threshold", 0.7)

def log_alert(packet):
    with open('alerts.json', 'a') as f:
        f.write(json.dumps(packet) + '\n')

def wait_for_anomaly_scores(bootstrap_servers='kafka:9092', timeout=60):
    start = time.time()
    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id=None,
                consumer_timeout_ms=1000
            )
            partitions = consumer.partitions_for_topic('anomaly_scores')
            if partitions:
                for p in partitions:
                    tp = TopicPartition('anomaly_scores', p)
                    consumer.assign([tp])
                    consumer.seek_to_end(tp)
                    if consumer.position(tp) > 0:
                        print("ML has produced to anomaly_scores, starting responder.")
                        consumer.close()
                        return
            consumer.close()
        except Exception:
            pass
        if time.time() - start > timeout:
            raise TimeoutError("Timed out waiting for ML to produce to anomaly_scores.")
        print("Waiting for ML to produce to anomaly_scores...")
        time.sleep(2)

wait_for_anomaly_scores()

# Use a unique consumer group ID for each run (optional, for isolation)
group_id = f"responder-group-{uuid.uuid4()}"

consumer = create_consumer_with_retry(
    'anomaly_scores',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='latest',
    group_id=group_id
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