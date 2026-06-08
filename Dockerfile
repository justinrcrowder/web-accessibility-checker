# Cloudflare Containers requires linux/amd64.
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

# Install dependencies first so they're cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Must listen on the port the Worker's Container class expects (defaultPort).
EXPOSE 8080

# Serve via gunicorn (the Flask dev server is not for production).
# 2 workers x 4 threads handles concurrent audits without much memory.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "60", "app:app"]
