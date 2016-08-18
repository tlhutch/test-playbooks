FROM java:8-jdk-alpine

ENV DOCKER_BUCKET get.docker.com
ENV DOCKER_VERSION 1.11.2
ENV DOCKER_SHA256 8c2e0c35e3cda11706f54b2d46c2521a6e9026a7b13c7d4b8ae1f3a706fc55e1

RUN apk add --update \
    curl \
    gcc \
    git \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssh-client \
    openssl-dev \
    py-pip \
    python \
    python-dev

RUN set -x \
    && curl -fSL "https://${DOCKER_BUCKET}/builds/Linux/x86_64/docker-$DOCKER_VERSION.tgz" -o docker.tgz \
    && echo "${DOCKER_SHA256} *docker.tgz" | sha256sum -c - \
    && tar -xzvf docker.tgz \
    && mv docker/* /usr/local/bin/ \
    && rmdir docker \
    && rm docker.tgz \
    && docker -v

RUN pip install --upgrade \
    ansible \
    boto \
    docker-compose \
    docker-py \
    requests==2.7.0

RUN curl -L https://storage.googleapis.com/kubernetes-release/release/v1.2.4/bin/linux/amd64/kubectl > /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

RUN curl -L http://repo.jenkins-ci.org/releases/org/jenkins-ci/plugins/swarm-client/2.2/swarm-client-2.2-jar-with-dependencies.jar > swarm-client-jar-with-dependencies.jar

RUN apk del --purge \
    gcc \
    linux-headers \
    musl-dev \
    openssl-dev \
    python-dev
