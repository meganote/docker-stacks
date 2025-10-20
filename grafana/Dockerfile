FROM docker.io/grafana/grafana:12.1.1

USER root
RUN  grafana cli --pluginUrl=https://github.com/grafana/traces-drilldown/releases/download/v1.2.0/grafana-exploretraces-app-1.2.0.zip plugins install grafana-traces-app
RUN  grafana cli --pluginUrl=https://github.com/grafana/opensearch-datasource/releases/download/v2.31.0/grafana-opensearch-datasource-2.31.0.linux_amd64.zip plugins install grafana-opensearch-datasource
RUN  grafana cli --pluginUrl=https://github.com/grafana/metrics-drilldown/releases/download/v1.0.18/grafana-metricsdrilldown-app-1.0.18.zip install grafana-metricsdrilldown-app

USER 472
