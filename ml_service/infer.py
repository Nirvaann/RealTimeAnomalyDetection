import json
import time
import socket
import numpy as np
import tensorflow as tf
import joblib
from kafka import KafkaConsumer, KafkaProducer, errors

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

def create_consumer_with_retry(*args, **kwargs):
    for i in range(10):
        try:
            return KafkaConsumer(*args, **kwargs)
        except errors.NoBrokersAvailable:
            print("Kafka not ready, retrying in 5 seconds...")
            time.sleep(5)
    raise RuntimeError("Kafka not available after multiple retries.")

model = tf.keras.models.load_model('autoencoder_model.keras')
scaler = joblib.load('scaler.save')

consumer = create_consumer_with_retry(
    'processed_packets',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='latest',
    group_id='ml-group'
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
    return scaler.transform([features]).astype(np.float32)

HIGH_ANOMALY_THRESHOLD = 1.5
POTENTIAL_ANOMALY_THRESHOLD = 0.4  # Lowered for more partials

def classify_packet(packet, score):
    if score > HIGH_ANOMALY_THRESHOLD:
        return "HIGH ANOMALY"
    elif score > POTENTIAL_ANOMALY_THRESHOLD:
        return "POTENTIAL ANOMALY"
    else:
        return "NORMAL"

for idx, msg in enumerate(consumer):
    sniffer_type = msg.value.get('sniffer_anomaly_type', 'unknown')
    vec = packet_to_vector(msg.value)
    recon = model.predict(vec)
    loss = tf.keras.losses.mse(vec, recon).numpy().mean()
    result = msg.value
    result['anomaly_score'] = float(loss)
    classification = classify_packet(result, loss)
    result['classification'] = classification

    print(f"[{idx+1}] SnifferType={sniffer_type} | ML={classification}: Score={loss:.4f} | Packet={result}")

    producer.send('anomaly_scores', value=result)

    if idx >= 9:
        break

producer.close()