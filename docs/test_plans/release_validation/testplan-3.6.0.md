# Tower 3.6.0: Release Test Plan

## Table of Contents

  * [Resources](#resources)
  * [Supported Platforms](#supported-platforms)
    * [Ansible Versions](#ansible-versions)
    * [Operating Systems Versions](#operating-systems-versions)
  * [Features Tested](#features-tested)
  * [Verifications Steps](#verifications-steps)
    * [Install](#install)
    * [Upgrade](#upgrade)
    * [Regression](#regression)
    * [Artifacts](#arfifacts)

## Resources

* 7 full-time engineers (Caleb, Danny, Elijah, Elyezer, John,  Mat, Yanis)
* Initial planning document for whole engineering org (API + UI + QE) [here](https://docs.google.com/spreadsheets/d/1NNTN-SBM23UQPZAH9HylKhYQBAoyIsDcTlvl_ItDzHs/edit#gid=762158314)
* Ansible Tower 3.6.0 Project [here](https://github.com/orgs/ansible/projects/8)

## Supported Platforms

### Ansible Versions

  * stable.2.6
  * stable-2.7
  * stable-2.8

### Operating Systems Versions

  * RHEL Derivatives 7.4+
  * RHEL Derivatives 8.0+

## Features Tested

### Remove Ubuntu support (Yanis/Elijah)

- [ ] Testing complete

### Remove /api/v1 (Elijah/Elyezer/Danny)

- [ ] Testing complete

### Upgrade Django 2.2 LTS and DJRF (Yanis/Danny)

- [ ] Testing complete

### Upgrade PostgreSQL to version 10 and psycopg (Yanis/Mat)

- [ ] Testing complete

### Upgrade Node LTS (Yanis/Danny)

- [ ] Testing complete

### Runner work (Mat/Elijah/Danny)

- [ ] Testing complete

### Remove Inventory computed field (Elijah/Elyezer)

- [ ] Testing complete

### Customizable notification (Mat/Yanis/John)

- [ ] Testing complete

### Workflow Pause / Approve (Elijah/Mat/Danny)

- [ ] Testing complete

### Performance data capturing and display (Yanis/Caleb/Danny)

- [ ] Testing complete

### SSL for PostgreSQL and RabbitMQ (Yanis/Elijah)

- [ ] Testing complete

### Webhooks in Tower (Elyezer/Danny)

- [ ] Testing complete

### CLI and SDK (Elijah/Elyezer/John)

- [ ] Testing complete

### Project branch on JT/WFJT (Yanis/Elyezer/Danny)

- [ ] Testing complete

### License key change (Elijah/Caleb/Danny)

- [ ] Testing complete


## Verifications steps

### Install

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster Bundle with isolated nodes
  * [ ] OpenShift Cluster


### Upgrade

To test upgrades, use the following pipelines:

  * OpenShift 3.3.x to Release: [Release 33 to devel - OpenShift - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-openshift-release-verification/)
  * OpenShift 3.4.x to Release: [Release 34 to devel - OpenShift - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2FRelease%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/)
  * Non-OpenShift 3.3.x to Release: [Release 33 to devel - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-release-verification/)
  * Non-OpenShift 3.4.x to Release: [Release 34 to devel - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release34-release-verification/)

  * [ ] 3.2.8 to 3.6.0
    * [ ] Bundle/Plain - Standalone
  * [ ] 3.3.{0-5} -> 3.6.0
    * [ ] Bundle/Plain - Standalone/Cluster
    * [ ] OpenShift
  * [ ] 3.4.{0-3} -> 3.6.0
    * [ ] Bundle/Plain - Standalone/Cluster
    * [ ] OpenShift
  * [ ] 3.5.{0-1} -> 3.6.0
    * [ ] Bundle/Plain - Standalone/Cluster
    * [ ] OpenShift


### Regression

  * [ ] UI regression
  * [ ] API regression - Standalone
  * [ ] API regression - Traditional Cluster
  * [ ] API regression - OpenShift Cluster
  * [ ] Tower social authentication regression completed (vm)
    * [ ] Google OAuth
    * [ ] GitHub
    * [ ] GitHub Org
    * [ ] GitHub Team
    * [ ] Azure OAuth
    * [ ] Radius
  * [ ] Tower SAML integration regression completed (vm)
  * [ ] Logging regression completed - cluster
  * [ ] Backup/restore successful - standalone
  * [ ] Backup/restore successful - traditional cluster
  * [ ] Backup/restore successful - OpenShift
  * [ ] Deploy tower with HTTPS+Load Balancer+Let's Encrypt + run tests against instance
  * [ ] Deploy tower in OpenShift with an external DB + run tests against instance

### Artifacts

Use this pipeline to verify: http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fbuild-artifacts-pipeline

  * [ ] AMI
  * [ ] Vagrant image
  * [ ] Documentation
