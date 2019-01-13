# Tower 3.5.0: Release Test Plan

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

* 6 full-time engineers (Danny, Elijah, Elyezer, John,  Mat, Yanis)
* Initial planning document for whole engineering org (API + UI + QE) [here](https://docs.google.com/spreadsheets/d/1Vo1lyIx_33Ad7TPqzO19NAe501CRcX0HTA0Rgepm5j0/edit#gid=782981019)

## Supported Platforms

### Ansible Versions

  * stable-2.5
  * stable.2.6
  * stable-2.7

### Operating Systems Versions

  * RHEL Derivatives 7.4+
  * Ubuntu 16.04

## Features Tested

### Support RHEL 8, including Python 3 (Yanis/Elijah)

* Test Plan

- [ ] Testing complete

### Packaging for EL7/EL8 with Py3 (Yanis/Elijah)

* Test Plan

- [ ] Testing complete

### Replace supervisor (Elyezer/Mat)

* Test Plan

- [ ] Testing complete

### Use Brew Signed Packages (Yanis/Elyezer)

* Test Plan

- [ ] Testing complete

### Update social-auth dependencies for Google+ EOL (Mat/Elyezer)

* Test Plan

- [ ] Testing complete

### Move Tower to ansible-runner for task execution (Yanis/Danny)

* Test Plan

- [ ] Testing complete

### Using ansible-runner on isolated nodes (Yanis/Danny)

* Test Plan

- [ ] Testing complete

### Support become plugins (Elyezer/John)

* Test Plan

- [ ] Testing complete

### Replace inventory scripts with 2.6+ plugins (Elijah/Mat/Danny)

* Test Plan

- [ ] Testing complete

### Metrics! (Mat/Danny)

* Test Plan

- [ ] Testing complete

### Credential Plugins (Mat/John)

* Test Plan

- [ ] Testing complete

### Collect Ansible perf stats (Mat)

* Test Plan

- [ ] Testing complete

### License limits by org (Mat)

* Test Plan

- [ ] Testing complete

### Remove /api/v1 (Elyezer/Elijah)

* Test Plan

- [ ] Testing complete

### FIPS II: Cryptographic Boogaloo - use system crypto packages (Yanis)

* Test Plan

- [ ] Testing complete

### Handle new Ansible playbook stats (Mat)

* Test Plan

- [ ] Testing complete

## Verifications steps

### Install

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster Bundle with isolated nodes
  * [ ] OpenShift Cluster


### Upgrade

  * [ ] Standalone from latest minor
  * [ ] Standalone from latest major
  * [ ] Traditional Cluster with isolated nodes from latest minor
  * [ ] Traditional Cluster with isolated nodes from latest major
  * [ ] OpenShift Cluster from latest minor
  * [ ] OpenShift Cluster from latest major


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
  * [ ] Tower social authentication regression completed (OpenShift)
    * [ ] Google OAuth
    * [ ] GitHub
    * [ ] GitHub Org
    * [ ] GitHub Team
    * [ ] Azure OAuth
    * [ ] Radius
  * [ ] Tower SAML integration regression completed (OpenShift)
  * [ ] Logging regression completed - standalone
  * [ ] Logging regression completed - cluster
  * [ ] Backup/restore successful - standalone
  * [ ] Backup/restore successful - traditional cluster
  * [ ] Backup/restore successful - OpenShift


### Artifacts

  * [ ] AMI
  * [ ] Vagrant image
  * [ ] Documentation
