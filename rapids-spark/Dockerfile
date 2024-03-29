#
# Copyright (c) 2020-2022, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM nvidia/cuda:11.0.3-devel-ubuntu18.04
ARG spark_uid=185
ARG spark_version=3.2.1
ARG hadoop_version=hadoop3.2

# https://forums.developer.nvidia.com/t/notice-cuda-linux-repository-key-rotation/212771
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

# Install java dependencies
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-8-jdk openjdk-8-jre curl
ENV JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk-amd64
ENV PATH $PATH:/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/bin:/usr/lib/jvm/java-1.8.0-openjdk-amd64/bin

# Before building the docker image, first either download Apache Spark 3.1+ from
# http://spark.apache.org/downloads.html or build and make a Spark distribution following the
# instructions in http://spark.apache.org/docs/3.1.2/building-spark.html (see
# https://nvidia.github.io/spark-rapids/docs/download.html for other supported versions).  If this
# docker file is being used in the context of building your images from a Spark distribution, the
# docker build command should be invoked from the top level directory of the Spark
# distribution. E.g.: docker build -t spark:3.1.2 -f kubernetes/dockerfiles/spark/Dockerfile .

RUN set -ex && \
    ln -s /lib /lib64 && \
    mkdir -p /opt/spark && \
#    mkdir -p /opt/spark/jars && \
#    mkdir -p /opt/spark/examples && \
    mkdir -p /opt/spark/work-dir && \
    mkdir -p /opt/sparkRapidsPlugin && \
    touch /opt/spark/RELEASE && \
    rm /bin/sh && \
    ln -sv /bin/bash /bin/sh && \
    echo "auth required pam_wheel.so use_uid" >> /etc/pam.d/su && \
    chgrp root /etc/passwd && chmod ug+rw /etc/passwd

RUN curl -L https://archive.apache.org/dist/spark/spark-${spark_version}/spark-${spark_version}-bin-${hadoop_version}.tgz | tar -xz -C /opt/spark --strip-components=1

#COPY spark-${spark_version}/jars /opt/spark/jars
#COPY spark-${spark_version}/bin /opt/spark/bin
#COPY spark-${spark_version}/sbin /opt/spark/sbin
#COPY spark-${spark_version}/kubernetes/dockerfiles/spark/entrypoint.sh /opt/
#COPY spark-${spark_version}/examples /opt/spark/examples
#COPY spark-${spark_version}/kubernetes/tests /opt/spark/tests
#COPY spark-${spark_version}/data /opt/spark/data

RUN curl -L https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_2.12/0.5.0/rapids-4-spark_2.12-0.5.0.jar -o /opt/sparkRapidsPlugin/rapids-4-spark_2.12-0.5.0.jar && \
    curl -L https://repo1.maven.org/maven2/ai/rapids/cudf/0.19.2/cudf-0.19.2-cuda11.jar -o /opt/sparkRapidsPlugin/cudf-0.19.2-cuda11.jar
##COPY rapids-4-spark_2.12-*.jar /opt/sparkRapidsPlugin
COPY getGpusResources.sh /opt/sparkRapidsPlugin

#RUN rm -f /tmp/spark-${spark_version}.tgz
#
#RUN mkdir /opt/spark/python
# TODO: Investigate running both pip and pip3 via virtualenvs
RUN apt-get update && \
    apt install -y python python-pip && \
    apt install -y python3 python3-pip && \
    # We remove ensurepip since it adds no functionality since pip is
    # installed on the image and it just takes up 1.6MB on the image
    rm -r /usr/lib/python*/ensurepip && \
    pip install --upgrade pip setuptools && \
    # You may install with python3 packages by using pip3.6
    # Removed the .cache to save space
    rm -r /root/.cache && rm -rf /var/cache/apt/*

#COPY spark/python/pyspark /opt/spark/python/pyspark
#COPY spark/python/lib /opt/spark/python/lib

ENV SPARK_HOME /opt/spark

WORKDIR /opt/spark/work-dir
RUN chmod g+w /opt/spark/work-dir

ENV TINI_VERSION v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +rx /usr/bin/tini

RUN cp /opt/spark/kubernetes/dockerfiles/spark/entrypoint.sh /opt/ && \
    chmod +rx /opt/entrypoint.sh

ENTRYPOINT [ "/opt/entrypoint.sh" ]

# Specify the User that the actual main process will run as
USER ${spark_uid}
