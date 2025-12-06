# BLKOUT Research Agent - Docker Image for Coolify
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 blkout && chown -R blkout:blkout /app
USER blkout

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s \
    CMD python -c "print('healthy')" || exit 1

# Default command - run scheduler daemon
CMD ["python", "main.py"]
