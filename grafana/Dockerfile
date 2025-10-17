FROM docker.io/grafana/grafana:12.1.1

USER root
RUN apk add --no-cache wget unzip

USER 472
RUN wget -O /tmp/opensearch-plugin.zip \
    https://github.com/grafana/opensearch-datasource/releases/download/v2.31.0/grafana-opensearch-datasource-2.31.0.linux_amd64.zip
RUN mkdir -p /var/lib/grafana/plugins/grafana-opensearch-datasource && \
    unzip /tmp/opensearch-plugin.zip -d /var/lib/grafana/plugins/grafana-opensearch-datasource && \
    rm /tmp/opensearch-plugin.zip
    
ENV GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=grafana-opensearch-datasource
