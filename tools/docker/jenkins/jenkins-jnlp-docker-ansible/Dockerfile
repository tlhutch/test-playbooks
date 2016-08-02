FROM gcr.io/ansible-tower-engineering/docker-jnlp-slave:latest

ENV DOCKER_BUCKET get.docker.com
ENV DOCKER_VERSION 1.11.2
ENV DOCKER_SHA256 8c2e0c35e3cda11706f54b2d46c2521a6e9026a7b13c7d4b8ae1f3a706fc55e1

USER root

RUN set -x \
    && curl -fSL "https://${DOCKER_BUCKET}/builds/Linux/x86_64/docker-$DOCKER_VERSION.tgz" -o docker.tgz \
    && echo "${DOCKER_SHA256} *docker.tgz" | sha256sum -c - \
    && tar -xzvf docker.tgz \
    && mv docker/* /usr/local/bin/ \
    && rmdir docker \
    && rm docker.tgz \
    && docker -v

RUN apt-get update
RUN apt-get install -y \
    python-dev \
    libffi-dev \
    python-pip \
    libssl-dev

RUN pip install --upgrade cffi ansible boto docker-py

RUN curl -L https://github.com/docker/compose/releases/download/1.7.1/docker-compose-Linux-x86_64 > /usr/local/bin/docker-compose
RUN chmod +x /usr/local/bin/docker-compose

ADD jenkins.pub /home/jenkins/.ssh/id_rsa.pub

ENV HOME /home/jenkins
VOLUME /home/jenkins
WORKDIR /home/jenkins
