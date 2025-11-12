# FastAPI REST API
FROM python:3.11-slim

WORKDIR /app

# System deps (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy all files (main.py, utils, config, etc.)
COPY . /app

EXPOSE 9000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]