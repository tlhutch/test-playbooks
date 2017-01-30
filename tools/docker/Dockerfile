FROM frolvlad/alpine-glibc

ARG towerkit_dir='./tools/docker/.build/towerkit'
ARG tower_qa_dir='.'

RUN apk add --update \
    bash \
    ca-certificates \
    gcc \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssh-client \
    openssl-dev \
    py-pip \
    python \
    python-dev

RUN pip install --upgrade pip

COPY ${tower_qa_dir}/tests/requirements.txt /tower-qa/tests/requirements.txt
RUN pip install $(cat /tower-qa/tests/requirements.txt | grep -v towerkit)

COPY ${towerkit_dir}/requirements.txt /towerkit/requirements.txt
RUN pip install -r /towerkit/requirements.txt

COPY ${towerkit_dir} /towerkit
RUN pip install /towerkit

COPY ${tower_qa_dir} /tower-qa

WORKDIR /tower-qa

RUN apk del --purge \
    gcc \
    linux-headers \
    musl-dev \
    openssl-dev \
    python-dev
