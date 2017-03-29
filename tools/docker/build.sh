#!/bin/bash -xe

CONTAINER_IMAGE_NAME="${CONTAINER_IMAGE_NAME:-gcr.io/ansible-tower-engineering/tower-qe}"

TOWERKIT_REPO="${TOWERKIT_REPO:-https://github.com/ansible/towerkit}"
TOWERKIT_DIR="${TOWERKIT_DIR:-tools/docker/.build/towerkit}"

ansible localhost -i 'localhost,' -c local -o -m git -a \
    "repo=${TOWERKIT_REPO} dest=${TOWERKIT_DIR} version=master force=yes"

REV_TOWERKIT=$(git --git-dir="${TOWERKIT_DIR}/.git" rev-parse HEAD | head -c7)
REV_TOWER_QA=$(git rev-parse HEAD | head -c7)

docker build -f ./tools/docker/Dockerfile \
    --build-arg TOWERKIT_DIR="${TOWERKIT_DIR}" \
    --tag ${CONTAINER_IMAGE_NAME}:latest \
    --tag ${CONTAINER_IMAGE_NAME}:${REV_TOWERKIT}_${REV_TOWER_QA} .

docker push ${CONTAINER_IMAGE_NAME}:latest
docker push ${CONTAINER_IMAGE_NAME}:${REV_TOWERKIT}_${REV_TOWER_QA}

docker rmi $(docker images -f "dangling=true" -q) || :
