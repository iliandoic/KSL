FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install and build frontend
COPY ksl-web/package*.json ./ksl-web/
RUN cd ksl-web && npm install

COPY ksl-web/ ./ksl-web/
RUN cd ksl-web && npm run build

# Copy backend
COPY . .

# Start server - Railway provides PORT env var
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
