FROM tensorflow/tensorflow:2.19.0-gpu

WORKDIR /app
COPY ml_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml_service/infer.py .
COPY ml_service/scaler.save .
COPY ml_service/autoencoder_model.keras .

COPY ml_service/evaluate_autoencoder.py .
COPY ml_service/test_data.csv .

ENTRYPOINT ["sh", "-c", "python infer.py && python evaluate_autoencoder.py"]