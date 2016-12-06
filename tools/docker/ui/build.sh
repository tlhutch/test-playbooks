#!/bin/bash -xe

CONTAINER_IMAGE_NAME="${CONTAINER_IMAGE_NAME:-gcr.io/ansible-tower-engineering/tower-qe}"

ansible localhost -i 'localhost,' -c local -o -m git -a \
    "repo=git@github.com:ansible/towerkit.git
     dest=tools/docker/ui/.build/towerkit
     version=master
     ssh_opts='-o StrictHostKeyChecking=no'
     force=yes"

REV_TOWERKIT=$(git --git-dir=tools/docker/ui/.build/towerkit/.git rev-parse HEAD | head -c7)
REV_TOWER_QA=$(git rev-parse HEAD | head -c7)

docker build -f ./tools/docker/ui/Dockerfile \
    --tag ${CONTAINER_IMAGE_NAME}:latest \
    --tag ${CONTAINER_IMAGE_NAME}:${REV_TOWERKIT}_${REV_TOWER_QA} .

docker push ${CONTAINER_IMAGE_NAME}:latest
docker push ${CONTAINER_IMAGE_NAME}:${REV_TOWERKIT}_${REV_TOWER_QA}

docker rmi $(docker images -f "dangling=true" -q) || :
