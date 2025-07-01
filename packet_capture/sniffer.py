import pyshark
import json
import time
import socket
import os
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
    # Interleave normal and anomalous packets
    for i in range(10):
        if i % 3 == 0:  # Every third packet is anomalous
            features = {
                'src_ip': f'10.0.0.{i}',
                'dst_ip': f'8.8.8.{i}',
                'src_port': 4000 + i,
                'dst_port': 5000 + i,
                'protocol': 'XYZ',
                'length': 9999,
                'ttl': 2,
                'unknown_protocol': 1,
                'low_ttl_alert': 1,
                'potential_lateral_movement': 1,
                'timestamp': time.time()
            }
            print(f"Sent anomalous test packet: {features}")
        else:
            features = {
                'src_ip': f'192.168.1.{i}',
                'dst_ip': f'192.168.1.{i+1}',
                'src_port': 1000 + i,
                'dst_port': 2000 + i,
                'protocol': 'TCP',
                'length': 100 + i,
                'ttl': 64,
                'timestamp': time.time()
            }
            print(f"Sent normal test packet: {features}")
        producer.send('raw_packets', value=features)
        time.sleep(0.1)

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
