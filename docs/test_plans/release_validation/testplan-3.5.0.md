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

  * stable.2.6
  * stable-2.7

### Operating Systems Versions

  * RHEL Derivatives 7.4+
  * Ubuntu 16.04

## Features Tested

### Support RHEL 8, including Python 3 (Yanis/Elijah)

- [x] Testing complete

### Packaging for EL7/EL8 with Py3 (Yanis/Elijah)

- [x] Testing complete

### Replace supervisor (Elyezer/Mat)

- Not needed anymore. Supervisor 4 supports python3

### Use Brew Signed Packages (Yanis/Elyezer)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_brew_signed_packages.md)

- [ ] Testing complete

### Update social-auth dependencies for Google+ EOL (Mat/Elyezer)

- [x] Testing complete

### Move Tower to ansible-runner for task execution (Yanis/Danny)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_runner_integration.md)

- [x] Testing complete

### Using ansible-runner on isolated nodes (Yanis/Danny)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_runner_integration.md)

- [x] Testing complete

### Support become plugins (Elyezer/John)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_become_plugins.md)

- [x] Testing complete

### Replace inventory scripts with 2.6+ plugins (Elijah/Mat/Danny)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_inventory_plugins.md)

- [x] Testing complete

### Metrics! (Mat/Danny)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_metrics_and_analytics.md)

- [x] Testing complete

### Credential Plugins (Mat/John)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_credential_plugins.md)

- [x] Testing complete

### Collect Ansible perf stats (Mat)

- Punted to 3.6 release

### License limits by org (Mat)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_org_host_limits.md)

- [x] Testing complete

### Remove /api/v1 (Elyezer/Elijah)

- Punted to 3.6 release

### FIPS II: Cryptographic Boogaloo - use system crypto packages (Yanis)

- No change finally needed. Ansible does not ship paramiko anymore. Customer wanting is need to BYO paramiko - documentation has been updated to state that would not be FIPS compliant.

### Handle new Ansible playbook stats (Mat)

* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/35_new_ansible_stats.md)

- [x] Testing complete

## Verifications steps

### Install

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster Bundle with isolated nodes
  * [ ] OpenShift Cluster


### Upgrade

  * [ ] Check ansible version check that is [hardcoded in tower-packaging](https://github.com/ansible/tower-packaging/blob/f8d3d4cd6d1cf35cad6e09de88068440d667ff42/setup/roles/preflight/defaults/main.yml#L6)
  * [ ] 3.2.8 to 3.5.0
    * [ ] Bundle/Plain - Standalone/Cluster
  * [ ] 3.3.{0-5} -> 3.5.0
    * [ ] Bundle/Plain - Standalone/Cluster
    * [ ] OpenShift
  * [ ] 3.4.{0-3} -> 3.5.0
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
