# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.6
FROM python:${PYTHON_VERSION}-slim 

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Install gcc and other build dependencies.
RUN apt-get update && \
    apt-get install -y \
    procps \
    vim \
    gcc \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    livekit \
    livekit-agents \
    livekit-api \
    livekit-protocol \
    livekit-plugins-silero \
    livekit-plugins-deepgram \
    livekit-plugins-elevenlabs \
    livekit-plugins-openai
