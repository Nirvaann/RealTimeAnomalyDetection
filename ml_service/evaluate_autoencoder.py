import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.metrics import classification_report, confusion_matrix

MESSAGE_LIMIT = 20  # Total number of samples to evaluate

model = tf.keras.models.load_model('autoencoder_model.keras')
scaler = joblib.load('scaler.save')

test = pd.read_csv('test_data.csv')

# Sample equal number of normal and anomalous packets
normal = test[test['label'] == 0].sample(MESSAGE_LIMIT // 2, random_state=42)
anomaly = test[test['label'] == 1].sample(MESSAGE_LIMIT // 2, random_state=42)
test_balanced = pd.concat([normal, anomaly]).sample(frac=1, random_state=42)  # Shuffle

X_test = test_balanced[['length', 'ttl', 'unknown_protocol', 'low_ttl_alert', 'potential_lateral_movement']].values
y_true = test_balanced['label'].values

X_test_scaled = scaler.transform(X_test)
recon = model.predict(X_test_scaled)
losses = np.mean(np.square(X_test_scaled - recon), axis=1)

threshold = 0.2  # Use the same as in your pipeline
y_pred = (losses > threshold).astype(int)

print("Confusion Matrix:")
print(confusion_matrix(y_true, y_pred))
print("\nClassification Report:")
print(classification_report(y_true, y_pred))

print("\nDetailed Results ({} messages):".format(len(y_true)))
for i, (score, pred, true) in enumerate(zip(losses, y_pred, y_true)):
    print(f"[{i+1}] Score={score:.4f} | Predicted={pred} | Actual={true}")