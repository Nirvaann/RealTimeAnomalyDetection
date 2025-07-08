import os
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
from sklearn.metrics import classification_report, confusion_matrix

MESSAGE_LIMIT = 20  # Total number of samples to evaluate

# Ensure we are in the correct directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load model and scaler
model_path = os.path.join(SCRIPT_DIR, 'autoencoder_model.keras')
scaler_path = os.path.join(SCRIPT_DIR, 'scaler.save')
test_data_path = os.path.join(SCRIPT_DIR, 'test_data.csv')

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")
if not os.path.exists(scaler_path):
    raise FileNotFoundError(f"Scaler file not found: {scaler_path}")
if not os.path.exists(test_data_path):
    raise FileNotFoundError(f"Test data file not found: {test_data_path}")

model = tf.keras.models.load_model(model_path)
scaler = joblib.load(scaler_path)

test = pd.read_csv(test_data_path)

# Check for missing values and drop them if any
if test.isnull().values.any():
    print("Warning: NaN values found in test data! Dropping rows with NaN.")
    test = test.dropna()

# Sample equal number of normal and anomalous packets
if (test['label'] == 0).sum() < MESSAGE_LIMIT // 2 or (test['label'] == 1).sum() < MESSAGE_LIMIT // 2:
    raise ValueError("Not enough samples of each class in test data for balanced sampling.")

normal = test[test['label'] == 0].sample(MESSAGE_LIMIT // 2)
anomaly = test[test['label'] == 1].sample(MESSAGE_LIMIT // 2)
test_balanced = pd.concat([normal, anomaly]).sample(frac=1)  # Shuffle

X_test = test_balanced[['length', 'ttl', 'unknown_protocol', 'low_ttl_alert', 'potential_lateral_movement']].values
y_true = test_balanced['label'].values

X_test_scaled = scaler.transform(X_test)
recon = model.predict(X_test_scaled)
losses = np.mean(np.square(X_test_scaled - recon), axis=1)

threshold = 0.7  # Use the same as in your pipeline
y_pred = (losses > threshold).astype(int)

print("Confusion Matrix:")
print(confusion_matrix(y_true, y_pred))
print("\nClassification Report:")
print(classification_report(y_true, y_pred))

# ...existing code...

print("\nDetailed Results ({} messages):".format(len(y_true)))
for i, (score, pred, true) in enumerate(zip(losses, y_pred, y_true)):
    print(f"[{i+1}] Score={score:.4f} | Predicted={pred} | Actual={true}")


report = classification_report(y_true, y_pred, output_dict=True)
accuracy = (y_true == y_pred).mean()
precision_anomaly = report['1']['precision']
recall_anomaly = report['1']['recall']
f1_anomaly = report['1']['f1-score']

print("\nSummary:")
print("Classification Report")
print(f"Precision (for anomaly): {precision_anomaly:.2f}")
print("(All predicted anomalies were actually anomalies.)" if precision_anomaly == 1.0 else "")
print(f"Recall (for anomaly): {recall_anomaly:.2f}")
print(f"({recall_anomaly*100:.0f}% of actual anomalies were detected.)")
print(f"F1-score (for anomaly): {f1_anomaly:.2f}")
print("(Balance between precision and recall.)")
print(f"Accuracy: {accuracy:.2f}")
print(f"({accuracy*100:.0f}% of all predictions were correct.)")