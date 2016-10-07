#!/bin/bash -xe

# set up key for agent forwarding
eval `ssh-agent -s`
ssh-add /root/.ssh/cloud

ansible-playbook -e "ec2_public_key=/root/.ssh/cloud.pub" $*
