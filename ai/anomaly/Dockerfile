FROM python:3.12-slim

# Logs Python affichés tout de suite dans "docker compose logs"
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Par défaut : détection en temps réel. Les autres scripts se lancent avec
#   docker compose run --rm anomaly python train.py
CMD ["python", "detect.py"]
