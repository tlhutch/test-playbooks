FROM centos:7

ARG towerkit_dir='./tools/docker/.build/towerkit'
ARG tower_qa_dir='.'

RUN yum install -y epel-release

RUN yum install -y \
    bash \
    ca-certificates \
    gcc \
    gdb \
    openssl \
    openssl-devel \
    python \
    python-pip \
    python-devel

RUN pip install --upgrade pip

COPY ${tower_qa_dir}/tests/requirements.txt /tower-qa/tests/requirements.txt
RUN pip install $(cat /tower-qa/tests/requirements.txt | grep -v towerkit)

COPY ${towerkit_dir}/requirements.txt /towerkit/requirements.txt
RUN pip install -r /towerkit/requirements.txt

COPY ${towerkit_dir} /towerkit
RUN pip install -e /towerkit

COPY ${tower_qa_dir} /tower-qa

WORKDIR /tower-qa
