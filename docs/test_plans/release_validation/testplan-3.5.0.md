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
  * stable-2.8

### Operating Systems Versions

  * RHEL Derivatives 7.4+
  * RHEL Derivatives 8
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

  * [x] Standalone
  * [x] Standalone Bundle
  * [x] Traditional Cluster with isolated nodes
  * [x] Traditional Cluster Bundle with isolated nodes
  * [x] [OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Test_Tower_OpenShift_Deploy/detail/Test_Tower_OpenShift_Deploy/616/pipeline)


### Upgrade

To test upgrades, use the following pipelines:

  * OpenShift 3.3.x to Release: [Release 33 to devel - OpenShift - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-openshift-release-verification/)
  * OpenShift 3.4.x to Release: [Release 34 to devel - OpenShift - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2FRelease%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/)
  * Non-OpenShift 3.3.x to Release: [Release 33 to devel - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-release-verification/)
  * Non-OpenShift 3.4.x to Release: [Release 34 to devel - Release Verification](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release34-release-verification/)

  * [ ] Check ansible version check that is [hardcoded in tower-packaging](https://github.com/ansible/tower-packaging/blob/f8d3d4cd6d1cf35cad6e09de88068440d667ff42/setup/roles/preflight/defaults/main.yml#L6)
  * [ ] 3.2.8 to 3.5.0
    * [ ] Bundle/Plain - Standalone/Cluster
  * [x] 3.3.{0-5} -> 3.5.0
    * [x] [Bundle/Plain - Standalone/Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-release-verification/detail/upgrade-release33-release-verification/19/pipeline)
    * [x] [OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release33-openshift-release-verification/detail/upgrade-release33-openshift-release-verification/6/pipeline)
  * [x] 3.4.{0-3} -> 3.5.0
    * [x] [Bundle/Plain - Standalone/Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fupgrade-release34-release-verification/detail/upgrade-release34-release-verification/9/pipeline)
    * [x] [OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2FRelease%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/detail/Release%2034%20to%20devel%20-%20OpenShift%20-%20Release%20Verification/2/pipeline)


### Regression

  * [ ] UI regression
  * [ ] API regression - Standalone
  * [ ] API regression - Traditional Cluster
  * [ ] API regression - OpenShift Cluster
  * [x] Tower social authentication regression completed (vm)
    * [x] Google OAuth
    * [x] GitHub
    * [x] GitHub Org
    * [x] GitHub Team
    * [x] Azure OAuth
    * [x] Radius
  * [x] Tower SAML integration regression completed (vm)
  * [x] Logging regression completed - cluster
  * [x] Backup/restore successful - standalone
  * [x] Backup/restore successful - traditional cluster
  * [x] [Backup/restore successful - OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Test_Tower_OpenShift_Backup_And_Restore/detail/Test_Tower_OpenShift_Backup_And_Restore/19/)
  * [ ] Deploy tower with HTTPS+Load Balancer+Let's Encrypt + run tests against instance
  * [x] Deploy tower in OpenShift with an external DB + run tests against instance

### RHEL8

For this release RHEL8 is a special candidate as it is not GA yet and hence we have a set of different jobs to test it.
Other action (namely Backup And Restore) are manual - since the AMI is not available - and in order to no waste time writing
a script that will be throw away.

**Note**: This is used for QE Sign-Off. Those jobs should be run with traditionnal tower-qa scripts when RHEL8 AMI is GA and
before we cut the actual release for sanity checking

  * [x] [RHEL8 - Standalone - Plain Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/rhel8/job/Install%20And%20Integration%20RHEL8/125/)
  * [x] [RHEL8 - Standalone - Bundle Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/rhel8/job/Install%20And%20Integration%20RHEL8/128/)
  * [x] [RHEL8 - Cluster - Plain Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/rhel8/job/Install%20And%20Integration%20RHEL8/126/)
  * [x] [RHEL8 - Cluster - Bundle Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/rhel8/job/Install%20And%20Integration%20RHEL8/129/)
  * [x] RHEL8 - Backup And Restore - Standalone/PlainInstall (Manual)
  * [ ] RHEL8 - Standalone - API Regression
  * [ ] RHEL8 - Cluster - API Regression
  * [ ] RHEL8 - UI Regression


### Artifacts

Use this pipeline to verify: http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fbuild-artifacts-pipeline

  * [x] [AMI](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Build_Tower_Image/detail/Build_Tower_Image/109/pipeline/)
  * [x] [Vagrant image](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Build_Tower_Vagrant_Box/detail/Build_Tower_Vagrant_Box/65/pipeline/)
  * [x] [Documentation](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Build_Tower_Docs/detail/Build_Tower_Docs/3290/pipeline/)
