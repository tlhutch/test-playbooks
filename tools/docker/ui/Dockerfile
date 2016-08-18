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

ADD tests/requirements.txt /requirements.txt

RUN pip install -r requirements.txt

ADD . /tower-qa
WORKDIR /tower-qa

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
