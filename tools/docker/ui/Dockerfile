FROM gcr.io/ansible-tower-engineering/tower-qe

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

ADD . /tower-qa
WORKDIR /tower-qa

RUN chmod a+x tools/docker/ui/credentials.sh
RUN tools/docker/ui/credentials.sh

RUN chmod a+x tools/docker/ui/pytest_sauce.sh
RUN chmod a+x tools/docker/ui/pytest_local.sh
