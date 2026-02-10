# Use Python 3.11 Alpine image as base
FROM python:3.11.14-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
# build-base: gcc, g++, make and other build tools
# postgresql-dev: for psycopg
# libffi-dev: for various Python packages
# musl-dev: for compiling C extensions
RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    libffi-dev \
    musl-dev \
    linux-headers

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose the port that adk web will run on
EXPOSE 8000

# Set environment variables (can be overridden by docker-compose)
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')" || exit 1

# Run the adk web server
CMD ["sh", "-c", "adk web --host ${HOST} --port ${PORT}"]
