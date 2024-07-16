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
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    livekit~=0.11.1 \
    livekit-agents~=0.7.2 \
    livekit-api~=0.5.1 \
    livekit-protocol~=0.5.1 \
    livekit-plugins-silero~=0.5.3 \
    livekit-plugins-deepgram~=0.5.1 \
    livekit-plugins-elevenlabs~=0.6.0 \
    livekit-plugins-openai~=0.6.0
