# Dockerfile for S.P.O.T. FastAPI Backend Engine & SQLite DB Persistence
FROM python:3.11-slim

WORKDIR /app

# Install lightweight runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt-get/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code & seed database
COPY backend/ ./backend/

# Set Python path to ensure module imports resolve correctly
ENV PYTHONPATH=/app

# Expose FastAPI Uvicorn Port
EXPOSE 8000

# Seed database on boot if needed and launch Uvicorn backend
CMD ["sh", "-c", "python backend/seed_data.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
