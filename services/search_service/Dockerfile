FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update \
  && apt-get install -y --no-install-recommends openssl \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOCR_BASE_DIR=/hocr_mount/books
ENV SEARCH_SERVICE_BASE_URL=https://127.0.0.1:5001
ENV IIIF_SERVER_BASE_URL=https://127.0.0.1:5000

EXPOSE 5001

CMD ["sh", "-c", "mkdir -p /app/certs && if [ ! -f /app/certs/server.key ] || [ ! -f /app/certs/server.crt ]; then openssl req -x509 -newkey rsa:2048 -nodes -keyout /app/certs/server.key -out /app/certs/server.crt -days 365 -subj '/CN=127.0.0.1'; fi; exec gunicorn --bind 0.0.0.0:5001 --workers 4 --keyfile /app/certs/server.key --certfile /app/certs/server.crt app:app"]
