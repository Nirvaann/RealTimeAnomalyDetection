FROM tensorflow/tensorflow:2.15.0-gpu

WORKDIR /app

# Install Python and pip
RUN apt update && apt install -y python3 python3-pip

# Upgrade pip and install TensorFlow
RUN pip3 install --upgrade pip
RUN pip3 install tensorflow==2.15

# Install other requirements
COPY ml_service/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ml_service/infer.py .
COPY ml_service/scaler.save .
COPY ml_service/autoencoder_model.keras .


COPY ml_service/rand_test_data.py .
RUN python3 rand_test_data.py


COPY ml_service/evaluate_autoencoder.py .

ENTRYPOINT ["sh", "-c", "python3 rand_test_data.py && python3 infer.py && python3 evaluate_autoencoder.py"]