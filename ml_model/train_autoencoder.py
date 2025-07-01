import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import joblib

data = pd.read_csv('sample_data.csv', comment='#')

X = data[['length', 'ttl', 'unknown_protocol', 'low_ttl_alert', 'potential_lateral_movement']].values.astype(np.float32)

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X.shape[1],)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(8, activation='relu'),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(X.shape[1])
])

model.compile(optimizer='adam', loss='mse')
model.fit(X_scaled, X_scaled, epochs=30, batch_size=32)
model.save('../ml_service/autoencoder_model.keras', save_format='keras')

# Save the scaler for use in inference
joblib.dump(scaler, '../ml_service/scaler.save')