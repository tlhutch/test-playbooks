tower-qa playbooks
==================

This directory contains playbooks, roles and variables used for deploying a
Ansible Tower and related services.

## Dependencies

 * [ansible](https://github.com/ansible/ansible)

## Playbooks

 * `deploy-tower.yml` - Create cloud instances and install tower to each instance
 * `deploy-tower-ha.yml` - Create cloud instances, and install tower in an HA configuration
 * `network_partition.yml` - Creates a network partition between two sets of hosts

## Variable files

 * `images-ec2.yml` - variables to describe supported Amazon Machine Images (AMI)
 * `images-instance-isolated-groups.yml` - variables to describe an AWS-based Tower HA deployment with isolated groups

## Inventory

 * `inventory` - Ansible inventory file that describes a single localhost
 * `inventory-jenkins.py` - Ansible inventory script that loads inventory from the latest nightly `Test_Tower_Install` artifacts
