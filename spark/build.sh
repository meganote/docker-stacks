#!/usr/bin/env bash

set -ex

SPARK_VERSION=3.1.1
HADOOP_VERSION=hadoop3.2
AWS_JAVA_SDK_BUNDLE_VERSION=1.11.1034
HADOOP_AWS_VERSION=3.2.4

REPO=ghcr.io/meganote
TAG=v${SPARK_VERSION}-${HADOOP_VERSION}

wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-${HADOOP_VERSION}.tgz
tar -xvf spark-${SPARK_VERSION}-bin-${HADOOP_VERSION}.tgz

# Install additional jars
cd spark-${SPARK_VERSION}-bin-${HADOOP_VERSION}
wget -q -P ./jars https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_JAVA_SDK_BUNDLE_VERSION}/aws-java-sdk-bundle-${AWS_JAVA_SDK_BUNDLE_VERSION}.jar
wget -q -P ./jars https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar

# Build images
./bin/docker-image-tool.sh -r ${REPO} -t ${TAG} -p ./kubernetes/dockerfiles/spark/bindings/python/Dockerfile -X build
