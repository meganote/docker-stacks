FROM ubuntu:noble

ARG OPENCV_VERSION=4.9.0

ENV DEBIAN_FRONTEND noninteractive
RUN apt update --yes && \
    # - `apt-get upgrade` is run to patch known vulnerabilities in apt-get packages as
    #   the Ubuntu base image is rebuilt too seldom sometimes (less than once a month)
    apt upgrade --yes && \
    apt install --yes --no-install-recommends \
    git \
    cmake \
    pkg-config \
    build-essential \
    ant \
    openjdk-17-jdk \
    libopencv-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libavutil-dev \
    libswresample-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64

# build opencv
RUN git clone https://github.com/opencv/opencv.git && \
    cd opencv && \
    git checkout ${OPENCV_VERSION} && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_BUILD_TYPE=Release -D BUILD_SHARED_LIBS=OFF -D BUILD_JAVA=ON .. && \
    make -j8
