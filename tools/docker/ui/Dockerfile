FROM python:2.7

ARG GITHUB_USERNAME
ARG GITHUB_TOKEN

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
