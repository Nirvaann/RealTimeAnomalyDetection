import json
import time
import socket
from kafka import KafkaProducer

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

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def parse_conn_log(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) > 10:
                try:
                    data = {
                        'src_ip': parts[2],
                        'src_port': parts[3],
                        'dst_ip': parts[4],
                        'dst_port': parts[5],
                        'protocol': parts[6],
                        'length': int(parts[9]) + int(parts[10]),
                        'timestamp': float(parts[1]),
                        'ttl': 64
                    }
                    producer.send('raw_packets', value=data)
                except:
                    continue

if __name__ == "__main__":
    parse_conn_log('zeek_logs/conn.log')
