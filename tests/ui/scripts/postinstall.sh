#!/usr/bin/env bash

git clone --depth 1 https://github.com/ansible/awx.git awx
npm --prefix awx/awx/ui install

curl http://selenium-release.storage.googleapis.com/3.8/selenium-server-standalone-3.8.1.jar > bin/selenium-server-standalone.jar
