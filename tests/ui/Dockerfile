FROM python:2.7

ADD tests/requirements.txt /requirements.txt

RUN pip install -r requirements.txt

ADD . /tower-qa
WORKDIR /tower-qa

# https://github.com/docker/docker-py/issues/1117
RUN python setup.py clean
