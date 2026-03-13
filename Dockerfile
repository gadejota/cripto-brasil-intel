FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose port (Railway/Render injeta PORT via env)
EXPOSE 8000

# Start
CMD ["python", "server.py"]
