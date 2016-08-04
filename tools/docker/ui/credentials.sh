#!/bin/bash -xe

cat <<EOF>tests/credentials.yml
---
users:
  admin: &default_user
    username: admin
    password: fo0m4nchU
  default: *default_user

default: *default_user

ssh:
  username: root
  password: fake

github:
  completed:
    -'state:needs_test'
    -'state:test_in_progress'
    -'state:needs_docs'
  username: ${GITHUB_USERNAME:-} 
  token: ${GITHUB_TOKEN:-} 
EOF
