# Base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run migrations before starting FastAPI
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
