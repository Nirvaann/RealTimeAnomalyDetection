import pyshark
import json
import time
import socket
import os

import random
import uuid

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

interface = os.getenv("SNIFFER_INTERFACE", "eth0")

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def extract_flow_features(pkt):
    try:
        return {
            'src_ip': pkt.ip.src,
            'dst_ip': pkt.ip.dst,
            'src_port': pkt[pkt.transport_layer].srcport,
            'dst_port': pkt[pkt.transport_layer].dstport,
            'protocol': pkt.transport_layer,
            'length': int(pkt.length),
            'ttl': int(pkt.ip.ttl),
            'timestamp': time.time()
        }
    except Exception:
        return None
    
def capture_packets():
    for _ in range(10):
        is_anomalous = random.choice([True, False])  # Randomly decide the packet type

        features = {
            'packet_id': str(uuid.uuid4()),  # <-- Unique ID
            'type': 'anomalous' if is_anomalous else 'normal',  # <-- Label type
            'timestamp': time.time()
        }

        if is_anomalous:
            features.update({
                'src_ip': f'10.0.{random.randint(0, 255)}.{random.randint(1, 254)}',
                'dst_ip': f'8.8.{random.randint(0, 255)}.{random.randint(1, 254)}',
                'src_port': random.randint(4000, 6000),
                'dst_port': random.randint(5000, 7000),
                'protocol': random.choice(['XYZ', 'ABC', '???']),  # Unusual protocols
                'length': random.randint(5000, 15000),
                'ttl': random.randint(1, 10),  # Very low TTL
                'unknown_protocol': 1,
                'low_ttl_alert': 1,
                'potential_lateral_movement': 1
            })
            print(f"Sent anomalous test packet: {features}")
        else:
            features.update({
                'src_ip': f'192.168.{random.randint(0, 1)}.{random.randint(1, 254)}',
                'dst_ip': f'192.168.{random.randint(0, 1)}.{random.randint(1, 254)}',
                'src_port': random.randint(1000, 2000),
                'dst_port': random.randint(2000, 3000),
                'protocol': random.choice(['TCP', 'UDP', 'ICMP']),
                'length': random.randint(60, 1500),
                'ttl': random.randint(30, 128),
                'unknown_protocol': 0,
                'low_ttl_alert': 0,
                'potential_lateral_movement': 0
            })
            print(f"Sent normal test packet: {features}")

        producer.send('raw_packets', value=features)

        time.sleep(random.uniform(0.05, 0.2))  # <-- Jitter for realism


# def capture_packets():
#     cap = pyshark.LiveCapture(interface=interface)
#     for pkt in cap.sniff_continuously():
#         features = extract_flow_features(pkt)
#         if features:
#             producer.send('raw_packets', value=features)



# Add this to packet_capture/sniffer.py for testing
# def capture_packets():
#     for i in range(10):
#         features = {
#             'src_ip': f'192.168.1.{i}',
#             'dst_ip': f'192.168.1.{i+1}',
#             'src_port': 1000 + i,
#             'dst_port': 2000 + i,
#             'protocol': 'TCP',
#             'length': 100 + i,
#             'ttl': 64,
#             'timestamp': time.time()
#         }
#         producer.send('raw_packets', value=features)
#         print(f"Sent test packet: {features}")
#         time.sleep(0.1)



if __name__ == "__main__":
    capture_packets()
