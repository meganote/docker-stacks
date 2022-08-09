FROM ghcr.io/xiaomao23zhi/magnote-docker-stack/builder:main as builder

RUN MAVEN_OPTS="-Xss64m -Xmx2g -XX:ReservedCodeCacheSize=1g" && \
    git clone https://github.com/apache/spark.git --branch v3.3.0 --single-branch && \
    cd /spark && \
    dev/make-distribution.sh \
        --name hadoop-3.3.4-cloud-scala-2.12 --pip --r --tgz \
        -DskipTests -Dhadoop.version=3.3.4 \
        -Phive -Phive-thriftserver \
        -Phadoop-3.3.4 \
        -Phadoop-cloud \
        -Pkubernetes

FROM openjdk:11-jdk-slim
LABEL maintainer="Xiaomao23Zhi <xiaomao23zhi@gmail.com>"

COPY --from=builder spark-3.3.0-bin-hadoop-3.3.4-cloud-scala-2.12.tgz .
