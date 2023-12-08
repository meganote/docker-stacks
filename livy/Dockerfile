ARG LIVY_VERSION=0.8.0
ARG SPARK_VERSION=3.1.1
ARG HADOOP_VERSION=haoop3.2

FROM ghcr.io/meganote/livy-spark:v${LIVY_VERSION}_spark-${SPARK_VERSION}-${HADOOP_VERSION}

USER root
RUN cp $LIVY_CONF_DIR/log4j.properties.template $LIVY_CONF_DIR/log4j.properties && \
    mkdir -p $LIVY_HOME/work-dir && \
    mkdir /var/log/livy && \
    ln -s /var/log/livy $LIVY_HOME/logs

COPY conf/* $LIVY_CONF_DIR/
COPY entrypoint.sh /opt/
COPY Dockerfile /my_docker/

USER ${spark_uid}

#  8998 - Livy Server port
# 10000 - Livy RPC Server for Jupyter integration
EXPOSE 8998 10000

WORKDIR $LIVY_HOME/work-dir

ENTRYPOINT [ "/opt/entrypoint.sh" ]
