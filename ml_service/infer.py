import json
import time
import socket
import numpy as np
import tensorflow as tf
import joblib
from kafka import KafkaConsumer, KafkaProducer

print("Starting ML inference service...")  


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

model = tf.keras.models.load_model('autoencoder_model.keras')
scaler = joblib.load('scaler.save')

consumer = KafkaConsumer(
    'processed_packets',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',  # <-- Add this line
    group_id='ml-group'            # <-- Optionally add a group_id for offset management
)

producer = KafkaProducer(bootstrap_servers='kafka:9092',
                         value_serializer=lambda x: json.dumps(x).encode('utf-8'))

def packet_to_vector(packet):
    features = [
        packet['length'],
        packet.get('ttl', 64),
        int(packet.get('unknown_protocol', False)),
        int(packet.get('low_ttl_alert', False)),
        int(packet.get('potential_lateral_movement', False))
    ]
    # Normalize features using the same scaler as training
    return scaler.transform([features]).astype(np.float32)

# Set thresholds (you can tune these)
HIGH_ANOMALY_THRESHOLD = 0.2  # Lowered for testing, will flag more anomalies  # High anomaly (from responder/config/config.json)
POTENTIAL_ANOMALY_THRESHOLD = 0.5  # Potential anomaly

def classify_packet(packet, score):
    if score > HIGH_ANOMALY_THRESHOLD:
        return "HIGH ANOMALY"
    elif score > POTENTIAL_ANOMALY_THRESHOLD:
        return "POTENTIAL ANOMALY"
    else:
        return "NORMAL"

for idx, msg in enumerate(consumer):
    print(f"Received from processed_packets: {msg.value}")  # Show received message
    vec = packet_to_vector(msg.value)
    recon = model.predict(vec)
    loss = tf.keras.losses.mse(vec, recon).numpy().mean()
    result = msg.value
    result['anomaly_score'] = float(loss)
    classification = classify_packet(result, loss)
    result['classification'] = classification

    print(f"[{idx+1}] {classification}: Score={loss:.4f} | Packet={result}")

    producer.send('anomaly_scores', value=result)

    if idx >= 9:  # Only process 10 messages for demonstration
        break

producer.close()
