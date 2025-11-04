FROM python:3.13-slim

# Default envs (can be overridden in docker-compose)
ENV PUID=1000 \
    PGID=1000 \
    TZ=Etc/UTC

# Create a group & user that match host IDs
RUN groupadd -g ${PGID} appgroup \
    && useradd -u ${PUID} -g appgroup -m appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create config dirs
RUN mkdir -p /config \
    && chown -R appuser:appgroup /app /config

# Switch to non-root user
USER appuser

CMD [ "python", "run.py" ]
