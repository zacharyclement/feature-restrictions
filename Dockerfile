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

# Default command (can be overridden by docker-compose)
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
