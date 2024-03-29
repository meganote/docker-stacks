ARG MAVEN_BUILDER=ghcr.io/meganote/builder:v0.1.0
ARG SPARK_VERSION=3.1.1
ARG HADOOP_VERSION=hadoop3.2

### Livy Builder Container
FROM ${MAVEN_BUILDER} as build

ARG LIVY_GITHUB_REPO=xiaomao23zhi/incubator-livy
ARG LIVY_GITHUB_BRANCH=LIVY-327

RUN git clone https://github.com/${LIVY_GITHUB_REPO}.git --branch ${LIVY_GITHUB_BRANCH} --single-branch --depth=50 && \
    cd incubator-livy && \
    mvn clean package -B -V -e \
    -Pspark-3.1 \
    -Pthriftserver \
    -DskipTests \
    -DskipITs \
    -Dmaven.javadoc.skip=true && \
    cp assembly/target/apache-livy-0.8.0-incubating-SNAPSHOT-bin.zip /

### Final Container
FROM ghcr.io/meganote/spark-py:v${SPARK_VERSION}-${HADOOP_VERSION}

ARG spark_uid=185

ENV SPARK_HOME      /opt/spark
ENV SPARK_CONF_DIR  $SPARK_HOME/conf
ENV SPARK_CLASSPATH $SPARK_HOME/cluster-conf

COPY conf/* $SPARK_CONF_DIR/
# $SPARK_HOME/conf gets cleaned by Spark on Kubernetes internals, create and add to classpath another directory for logging and other configs
COPY conf/* $SPARK_HOME/cluster-conf/
COPY entrypoint.sh /opt/

ARG LIVY_VERSION_ARG=0.8.0-incubating-SNAPSHOT

ENV LIVY_VERSION            $LIVY_VERSION_ARG
ENV LIVY_HOME               /opt/livy
ENV LIVY_CONF_DIR           $LIVY_HOME/conf
ENV PATH                    $PATH:$LIVY_HOME/bin

# install livy
COPY --from=build /apache-livy-${LIVY_VERSION}-bin.zip /

USER root
RUN apt-get install -y unzip && \
    unzip /apache-livy-${LIVY_VERSION}-bin.zip -d / && \
    mv /apache-livy-${LIVY_VERSION}-bin /opt/ && \
    rm -rf $LIVY_HOME && \
    ln -s /opt/apache-livy-${LIVY_VERSION}-bin $LIVY_HOME && \
    rm -f /apache-livy-${LIVY_VERSION}-bin.zip

USER ${spark_uid}

#  4040 - Spark UI port
#  7078 - Driver RPC port
#  7079 - Blockmanager port
#  8088 - JMX Exporter for Prometheus
# 10000 - Livy RPC Server for Jupyter integration
# 10015 - Spark Thrift server port
EXPOSE 4040 7078 7079 8088 10000 10015
