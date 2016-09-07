FROM frolvlad/alpine-glibc

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

RUN apk add --update \
    bash \
    ca-certificates \
    gcc \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssl-dev \
    py-pip \
    python \
    python-dev

ADD . /tower-qa
WORKDIR /tower-qa

RUN pip install tower_qe/
RUN pip install -r tests/requirements.txt

RUN chmod a+x tools/docker/ui/credentials.sh
RUN tools/docker/ui/credentials.sh

RUN chmod a+x tools/docker/ui/pytest_sauce.sh
RUN chmod a+x tools/docker/ui/pytest_local.sh

# https://github.com/docker/docker-py/issues/1117
RUN python setup.py clean

RUN apk del --purge \
    gcc \
    linux-headers \
    musl-dev \
    openssl-dev \
    python-dev
