FROM python:3.10-slim-bullseye

RUN pip install --no-cache-dir kafka-python

WORKDIR /app
COPY zeek_ingestor/zeek_ingestor.py .
COPY zeek_ingestor/zeek_logs/ ./zeek_logs/

ENTRYPOINT ["python", "zeek_ingestor.py"]