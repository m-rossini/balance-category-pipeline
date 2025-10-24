# === Builder stage ===
FROM python:3.13.7-slim-bookworm AS builder

WORKDIR /app

# Update base packages and install minimal build deps so that installed wheels are built against updated libs
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./
# Copy package sources so Poetry can find the packages declared in pyproject.toml
COPY src/ ./src/

# Install Poetry (pin to a modern compatible version), configure to avoid virtualenv creation,
# and install only the main dependencies (replace removed --no-dev with --only main)
RUN pip install "poetry>=1.8.0" \
    && poetry config virtualenvs.create false \
    && poetry install --only main

# === Runtime stage ===
FROM python:3.13.7-slim-bookworm

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System dependencies: use non-interactive frontend, upgrade packages, install minimal set without recommended extras
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        iputils-ping \
        netcat-openbsd \
        make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed libs and binaries from builder (builder contains built wheels)
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY . .

# Run the app directly with python (no Poetry required at runtime)
CMD ["python", "-m", "balance"]

