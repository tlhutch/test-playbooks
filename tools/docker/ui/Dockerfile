FROM frolvlad/alpine-glibc

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

COPY ./tests/requirements.txt /tower-qa/tests/requirements.txt
RUN pip install -r /tower-qa/tests/requirements.txt

WORKDIR /tower-qa

RUN apk del --purge \
    gcc \
    linux-headers \
    musl-dev \
    openssl-dev \
    python-dev
