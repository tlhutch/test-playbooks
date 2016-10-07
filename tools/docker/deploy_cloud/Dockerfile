FROM gcr.io/ansible-tower-engineering/tower-qe

RUN apk add --update openssh
RUN ssh-keygen -f /root/.ssh/cloud -t rsa -N ''
RUN cat /root/.ssh/cloud.pub
ADD tools/docker/deploy_cloud/config /root/.ssh/config
RUN chmod 600 /root/.ssh/config

ADD . /tower-qa
WORKDIR /tower-qa

RUN chmod a+x tools/docker/deploy_cloud/deploy.sh
