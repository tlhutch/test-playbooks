tower-qa playbooks
=========================

This directory contains playbooks, roles and variables used for deploying a
Ansible Tower and related services.

## Dependencies
 * [ansible](https://github.com/ansible/ansible)

## Playbooks

 * `tower.yml` - Install Tower
 * `deploy-tower.yml` - Create cloud instances and install tower to each instance
 * `deploy-cloud.yml` - Create cloud instances
 * `destroy-cloud.yml` - Terminate cloud instances
 * `deploy-ha.yml` - Create cloud instances, and install tower in an HA configuration

## Variable files

 * `credentials.yml` - credentials needed for various cloud providers
 * `images-azure.py` - variables to describe supported Microsoft Azure instances
 * `images-ec2.py` - variables to describe supported Amazon Machine Images (AMI)
 * `images-gce.py` - variables to describe supported Google Compute Engine instances
 * `images-ha.py` - variables to describe an AWS-based Tower HA deployment
 * `images-rax.py` - variables to describe supported Rackspace Cloud Servers
 * `images-rds.py` - variables to describe an AWS RDS instance

## Inventory

 * `inventory` - Inventory file that describes a single localhost
 * `inventory-vmfusion` - Inventory script that returns active VMware Fusion hosts
