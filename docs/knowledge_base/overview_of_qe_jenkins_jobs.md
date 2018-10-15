# Overview of QE Jenkins Jobs

We use Jenkins to manage the running of our automated tests.
[http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#)

Note that in order to access the above link you will need to be on the Red Hat VPN.


The QE team as a whole maintains the jobs below. The team uses a weekly rotation to review test results, write up regressions, and repair issues with the tests themselves. You’ll sometimes hear the team refer to this as “the integration button” (which figuratively gets passed around). A description of the integration triage process is available [here](https://docs.google.com/document/d/1trChK3DScws2vJqEMMHdy3B0_9mHYcyxpZSbTlTq04k/edit). We had a meeting on 10/1/18 to ‘reboot’ the integration button - a recording of the meeting is available [here](https://bluejeans.com/s/PmDs3/).

## Main integration

- [Test_Tower_Integration](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration/) - Runs the full suite of regression tests against the current version of tower in development against a matrix that includes all supported platforms and all supported versions of Ansible Core.
- [Test_Tower_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Bundle_Install/) - Provisions instances used by the above integration job
- Build Jobs
	- [Test_Tower_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_TAR/) - prepares a tar file that contains the Tower install script (and associated Ansible playbooks / roles).
	- [Test_Tower_RPM](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_RPM/) - prepares Tower RPM package
	- [Test_Tower_DEB](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_DEB/) - prepares Tower Debian package
	- [Test_Tower_Bundle_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Bundle_TAR/) - prepares a install that bundles requirements
- [Nightly_Tower](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Nightly_Tower/) - triggers downstream build, install, and test jobs

## Cluster integration

Runs full integration including a suite of tests explicitly for clustered Tower. Clustered Tower refers to a traditional cluster installation on bare metal or vms. A separate test pipeline focuses on a Tower cluster deployment in Red Hat OpenShift.

- [Test_Tower_Install_Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Install_Cluster/)
- [Test_Tower_Integration_Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Cluster/)

## OpenShift

Performs an installation of Tower in OpenShift nightly and then runs integration against this newly provisioned instance. Tower is deployed in a clustered setup.

- [Test_Tower_OpenShift_Deploy](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Deploy/)
- [Test_Tower_OpenShift_Integration](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Integration/)

We use the [tower-qe](https://console.openshift.ansible.eng.rdu2.redhat.com/console/project/tower-qe/overview) OpenShift project for this and you will need credentials to access this project. Come ask chrwang@redhat.com for credentials for this.

## Patch Integration

Runs full integration against the latest patch release on a weekly basis. Pipeline is capable of running in parallel with main integration allowing the team to gather results for a main release and maintenance release.

- [Test_Tower_Integration_Patch](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Patch/)
- [Test_Tower_Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install/#) provisions instances for both main integration and the above patch job.
- [Nightly_Tower_Patch](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Nightly_Tower_Patch/) - triggers patch installs and tests each Sunday afternoon

## Tower Upgrade

Upgrades from the previous stable release on all supported platforms.

- [Test_Tower_Upgrade](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Upgrade/)

## Backup and Restore

Deploys a Tower instance, uses a python script to load the instance with a variety of resources, backs up this instance, deploys a separate instance, performs a restore, and runs another python script to confirm the resources created on the first instance have been restored.

- [Test_Tower_Backup_and_Restore](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Backup_and_Restore/)

## Bundle Installer

- [Test_Tower_Bundle_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Bundle_Install/) - confirms Tower bundle installer deploys Tower successfully. Job provisions Tower but is not followed by any additional testing.

## Ansible Core / Ansible Tower Product Integration Tests

Installs the latest release of Tower against Ansible development branches. Runs a subset of full integration that exercises the contact points between Tower and Ansible. Used by Tower team to sign-off on Ansible releases. A subset of the install / test jobs are triggered each night based on which development branches were changed in the past day.

- Ansible build jobs (maintained by Ansible Core team)
	- [Stable_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Stable_Ansible/) / [Nightly_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Nightly_Ansible/) - trigger downstream build / install / test jobs
	- [Build_Ansible_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_TAR/)
	- [Build_Ansible_Public_RPM](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_Public_RPM/)
	- [Build_Ansible_DEB](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_DEB/)
- [Ansible_Tower_Integration_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Install/)
- [Ansible_Tower_Integration_Test](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Test/)

## UI Test Pipeline

[Test_Tower_E2E_Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E_Pipeline/) - Runs the e2e ui tests

- Trigger: checks for scm changes against tower/release_X every 2 hours.
- Build: Builds RPM
- Deploy: Uses the Ansible Tower Jenkins plugin to deploy a RPM build to GCE
- Test: Runs the Test_Tower_E2E job against the GCE build
- Notify: Sends a slack notification to #e2e-resuts and notifies of failure or return-to-success in #ui-talk
[Test_Tower_E2E](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E/) - General E2E test execution utility job. Requires a FQDN, username, password
Used as a part of the Test_Tower_E2E_Pipeline
Used after the Openshift Integration runs
Soon: Used post-upgrade pipeline

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Oct 15, 2018.
