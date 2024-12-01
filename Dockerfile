# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Expose port for FastAPI
EXPOSE 8000

# Run both FastAPI server and Redis stream consumer
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4 & python stream_consumer.py"]
