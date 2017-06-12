FROM centos:7

ARG TOWERKIT_DIR

RUN yum install -y epel-release

RUN yum install -y \
    bash \
    ca-certificates \
    gcc \
    gdb \
    libffi-devel \
    openssl \
    openssl-devel \
    python \
    python-pip \
    python-devel

RUN pip install --upgrade pip

COPY requirements.txt /tower-qa/requirements.txt
RUN pip install $(cat /tower-qa/requirements.txt | grep -v towerkit)

COPY ${TOWERKIT_DIR}/requirements.txt /towerkit/requirements.txt
RUN pip install -r /towerkit/requirements.txt

COPY ${TOWERKIT_DIR} /towerkit
RUN pip install -e /towerkit

COPY . /tower-qa

WORKDIR /tower-qa
