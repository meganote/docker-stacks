FROM python:3.12-slim

ARG APP_DIR=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_DIR}
RUN pip install uv && \
    git clone https://github.com/bytedance/trae-agent.git ${APP_DIR} && \
    cd trae-agent && \
    uv sync --all-extras
