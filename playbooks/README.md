tower-qa playbooks
=========================

This directory contains playbooks, roles and variables used for deploying a
Ansible Tower and related services.

## Dependencies
 * [ansible](https://github.com/ansible/ansible)

## Playbooks

 * `deploy.yml` - Create cloud instances
 * `destroy.yml` - Terminate cloud instances
 * `deploy-ansible.yml` - Create cloud instances and install ansible
 * `deploy-tower.yml` - Create cloud instances and install tower to each instance
 * `deploy-tower-ldap.yml` - Create cloud instances, and install tower in an LDAP configuration
 * `deploy-tower-ha.yml` - Create cloud instances, and install tower in an HA configuration
 * `install-tower.yml` - Install Tower to an already provisioned system

## Variable files

 * `credentials.yml` - credentials needed for various cloud providers
 * `images-azure.yml` - variables to describe supported Microsoft Azure instances
 * `images-ec2.yml` - variables to describe supported Amazon Machine Images (AMI)
 * `images-gce.yml` - variables to describe supported Google Compute Engine instances
 * `images-rds.yml` - variables to describe an AWS RDS instance
 * `images-ha.yml` - variables to describe an AWS-based Tower HA deployment
 * `images-ldap.yml` - variables to describe an AWS-based Tower LDAP deployment

## Inventory

 * `inventory` - Ansible inventory file that describes a single localhost
 * `inventory-vmfusion.py` - Ansible inventory script that returns active VMware Fusion hosts
 * `inventory-jenkins.py` - Ansible inventory script that loads inventory from the latest nightly `Test_Tower_Install` artifacts
