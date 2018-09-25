#!/bin/bash -xe

git remote add tower git@github.com:ansible/tower.git

git push tower devel
