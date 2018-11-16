#!/usr/bin/env bash
set -euxo pipefail

git remote add tower git@github.com:ansible/tower.git

git push tower devel
