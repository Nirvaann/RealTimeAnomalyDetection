import pandas as pd
import numpy as np
import os

def random_packet(label):
    if label == 0:
        # Normal packet: values similar to training data, with some noise
        return {
            'length': int(np.random.normal(130, 15)),  # mean 130, std 15
            'ttl': int(np.random.normal(62, 2)),       # mean 62, std 2
            'unknown_protocol': 0,
            'low_ttl_alert': 0,
            'potential_lateral_movement': np.random.choice([0, 1], p=[0.8, 0.2])
        }
    else:
        # Mild/Moderate anomaly: values just outside normal range
        return {
            'length': int(np.random.choice([np.random.randint(180, 250), np.random.randint(60, 90)])),
            'ttl': int(np.random.choice([np.random.randint(5, 15), np.random.randint(70, 90)])),
            'unknown_protocol': np.random.choice([0, 1], p=[0.5, 0.5]),
            'low_ttl_alert': np.random.choice([0, 1], p=[0.5, 0.5]),
            'potential_lateral_movement': 1
        }

def generate_dataset(n_total=200, out_file=None):
    if out_file is None:
        out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data.csv')
    # Randomize anomaly ratio between 10% and 50%
    anomaly_ratio = np.random.uniform(0.1, 0.5)
    n_anomaly = int(n_total * anomaly_ratio)
    n_normal = n_total - n_anomaly
    print(f"Generating {n_total} packets: {n_normal} normal, {n_anomaly} anomaly (anomaly ratio: {anomaly_ratio:.2f})")

    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    data = []
    for _ in range(n_normal):
        pkt = random_packet(0)
        pkt['label'] = 0
        data.append(pkt)
    for _ in range(n_anomaly):
        pkt = random_packet(1)
        pkt['label'] = 1
        data.append(pkt)
    np.random.shuffle(data)
    df = pd.DataFrame(data)
    cols = ['length', 'ttl', 'unknown_protocol', 'low_ttl_alert', 'potential_lateral_movement', 'label']
    df = df[cols]
    if df.isnull().values.any():
        print("Warning: NaN values found in generated data!")
        df = df.fillna(0)
    df.to_csv(out_file, index=False)
    print(f"Generated {n_total} packets in {out_file}")

if __name__ == "__main__":
    generate_dataset()