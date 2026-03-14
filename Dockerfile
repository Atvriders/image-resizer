FROM python:3.12-slim

WORKDIR /app

# Install native libs Pillow needs for full format support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-turbo-progs \
    libpng-dev \
    libwebp-dev \
    libtiff-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cached layer)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ .

# Non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
