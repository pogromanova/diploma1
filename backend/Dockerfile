FROM python:3.9-slim as base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0.0.0.0:8000"]