FROM ghcr.io/agent-infra/sandbox:1.0.0.152

# Install
RUN npm install -g \
    pnpm \
    edgeone \
    @anthropic-ai/claude-code \
    @musistudio/claude-code-router \
    --registry=https://registry.npmmirror.com \
    && \
    npm cache clean --force

RUN mkdir -p /home/$USER/.claude-code-router/plugins
COPY .claude-code-router/config.json /home/$USER/.claude-code-router/config.json

COPY run.sh /opt/gem/run.sh
RUN chmod +x /opt/gem/run.sh
