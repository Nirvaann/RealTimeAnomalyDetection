#Acts as an intermediary that enriches or pre-processes the raw packets received from
#Kafka. Reads from raw_packets, adds additional metadata, and sends to processed_packets.
import time
import socket
import json
from kafka import KafkaConsumer, KafkaProducer

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

consumer = KafkaConsumer(
    'raw_packets',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',  # Start from latest messages if no committed offset
    enable_auto_commit=True,
    group_id='processor-group'   # Add a group id for offset management
)

producer = KafkaProducer(bootstrap_servers='kafka:9092',
                         value_serializer=lambda x: json.dumps(x).encode('utf-8'))

INTERNAL_IP_PREFIX = '192.168.'

def is_internal(ip):
    return ip.startswith(INTERNAL_IP_PREFIX)

def enrich_packet(packet):
    # Lateral movement detection
    if is_internal(packet['src_ip']) and is_internal(packet['dst_ip']):
        packet['potential_lateral_movement'] = True
    # TTL anomaly detection
    if packet.get('ttl', 64) < 10:
        packet['low_ttl_alert'] = True
    # Unknown protocol detection
    if packet['protocol'] not in ['TCP', 'UDP', 'ICMP']:
        packet['unknown_protocol'] = True
    packet['enriched'] = True
    return packet



max_messages = 10
count = 0
try:
    for msg in consumer:
        print(f"Received from raw_packets: {msg.value}")  # Show received message
        enriched = enrich_packet(msg.value)
        try:
            producer.send('processed_packets', value=enriched)
            producer.flush()
            print(f"Sent to processed_packets: {enriched}")  # Show sent message
        except Exception as e:
            print(f"Error sending to Kafka: {e}")
        count += 1
        if count >= max_messages:
            print(f"Processed {max_messages} messages, exiting.")
            break
except KeyboardInterrupt:
    print("Processor shutting down.")
    consumer.close()
    producer.close()

# try:
#     for msg in consumer:
#         enriched = enrich_packet(msg.value)
#         try:
#             producer.send('processed_packets', value=enriched)
#             producer.flush()
#             print(f"Sent to processed_packets: {enriched}")  # Add this line
#         except Exception as e:
#             print(f"Error sending to Kafka: {e}")
# except KeyboardInterrupt:
#     print("Processor shutting down.")
#     consumer.close()
#     producer.close()
