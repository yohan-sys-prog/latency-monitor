FROM python:3.12-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-warn-script-location \
    -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    LATENCY_MONITOR_PORT=8000 \
    LATENCY_MONITOR_HOST=0.0.0.0

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=5)"

# Use gunicorn for production (fallback to Flask dev server if gunicorn not available)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 'application.dashboard:app' || python3 -m application.dashboard"]
