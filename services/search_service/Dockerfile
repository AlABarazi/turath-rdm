FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HOCR_BASE_DIR=/hocr_mount/books
ENV SEARCH_SERVICE_BASE_URL=https://127.0.0.1:5001
ENV IIIF_SERVER_BASE_URL=https://127.0.0.1:5000

EXPOSE 5001

CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "app:app"]
