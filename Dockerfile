FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/ZakesB/dbsyncx"
LABEL org.opencontainers.image.description="Sync and backup PostgreSQL databases like Git."
LABEL org.opencontainers.image.licenses="MIT"

# Install PostgreSQL client tools (pg_dump, pg_restore, psql)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        cron && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

# Default configuration location
ENV DBSYNCX_CONFIG=/config/config.yaml

# Create directories for configuration and backups
RUN mkdir -p /config /backups

# Persistent mount points
VOLUME ["/config", "/backups"]

ENTRYPOINT ["dbsyncx"]
CMD ["--help"]