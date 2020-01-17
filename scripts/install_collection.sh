#!/usr/bin/env bash

set -exo pipefail

if [ -z "$1" ] ; then
     echo "Please pass the path to your clone of awx as an argument"
     exit 1
fi

awx_path="$1"

VERSION="$(cat $awx_path/VERSION)"

# Setup collection for the collection tests

cd $awx_path && make build_collection && make install_collection
docker exec -u 0 -it tools_awx_1 sh -c \
    "rm -rf /usr/share/ansible/collections/ansible_collections/awx/awx && \
    ansible-galaxy collection install awx_collection/awx-awx-$VERSION.tar.gz -p /usr/share/ansible/collections && \
    chmod go+r -R /usr/share/ansible/collections"

set -e
