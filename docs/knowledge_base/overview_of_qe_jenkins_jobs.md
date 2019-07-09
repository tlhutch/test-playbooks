# Overview of QE Jenkins Jobs

* [Introduction](#introduction)
* [General Practices](#general-practices)
* [Release Verification](#release-verification)
* [Ansible Core Compatibility](#ansible-core-compatibility)
* [List of Jenkins jobs](#list-of-jenkins-jobs)
* [YOLO](#yolo)
* [FAQ](#faq)


## Introduction

Ansible Tower QE team relies Jenkins to manage the running of our automated tests.
[http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#)

In order to access the above link you will need to be on the Red Hat VPN. One logs in with his kerberos credentials.
If you are presented with a page saying Unauthorized used, please reach out to Frank Jansen or Graham Mainwaring.

The QE team as a whole maintains the pipelines and jobs listed [below](list-of-jenkins-jobs).


## General Practices

The Ansible Tower QE team follows a certain number of general practices so our code base remains consistent:

  * Every new job created should be a Jenkins **Declarative** Pipeline.
  * Every step taken should be done in a shell script stored under git (`tools/jenkins/scripts/`) that one can run from his workstation.
  * No Jenkins specific feature should be used. We should be able to switch from Jenkins to any build system at any given time.
  * Unless you are certain nobody uses your Job, do not remove a job but move it to the Trash folder.
  * While creating a new pipeline, please create it on the `qe-sandbox` folder until it is ready.


## Release Verification

One of our main goal in the Tower QE team is to ensure we ship great quality software in a timely maneer.
To do that we want to have constant feedback about a release health during its development cycle, this is why
the Ansible Tower QE team runs the "final" release verification process nightly and ensure its always passing.

The actual job from Jenkins being triggered is the [Release Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Frelease-pipeline/activity) located in `Pipelines/Release`.
The code for this pipeline is availabe at [tools/jenkins/pipelines/release.groovy](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/release.groovy)
This verification process consists of the following actions:

  * Building the various artifacts (RPM, Installer, Bundle Installer, Documentation, AMI Image, Vagrant Image)
  * Testing minor and major upgrade for all supported scenarios (bundle, non bundle, standalone, cluster)
  * Testing backup and restore for all supported scenarios (bundle, non bundle, standalone, cluster)
  * Running integration testing for all supported scenarios (bundle, non bundle, standalone, cluster)

The results of this process is available in our dashboard: http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/releases

For each supported permutation of Operating System version and Ansible version, there is a colored bullet that indicates the status of the latest pipeline run:

  * **Yellow**: All upgrades, backup and restore and installation went fine. Some failures have been observed while running the integration test suite.
  * **Red**: One of the upgrades, backup and restore or installation failed. It didn't get to running the integration test suite.
  * **Green**: Everything is ok and operational. You can move on !

By clicking on the status orb one will be directed to a Jenkins blue ocean view of the pipeline that one can interact with to get all the information one needs.

Not every permutation runs the full test suite, only the one that are run with latest Ansible stable version.
The other permutations will be run with the `yolo or ansible_integration` pytest filter.

As stated earlier, this release verification process is run on a timely maneer, this is the logic used:

  * `devel`: nightly
  * Latest Released version ongoing maintenance release: nightly
  * Latest - 2: weekly
  * Latest - 3: weekly

This is an example of the cron definition at the time of the writing (`devel` being future `3.6.0`):

**Note**: This is the responsability of all the team members to ensure those test remains green at all time or that if not the team is aware of the reason why it can't be green.

```
H 18 * * * % TOWER_VERSION=devel
H 18 * * * % TOWER_VERSION=3.5.x
H H * * 6 % TOWER_VERSION=3.4.x
H H * * 7 % TOWER_VERSION=3.3.x
```

Finally, by default `latest` is selected as scope. This means only the latest versions of the supported Operating System are run.
If one wants to run **all** the supported Operating Systems, then one will need to choose `full` as the scope value.


## Ansible Core Compatibility

Installs the latest release of Tower against Ansible development branches. Runs a subset of full integration that exercises the contact points between Tower and Ansible. Used by Tower team to sign-off on Ansible releases. A subset of the install / test jobs are triggered each night based on which development branches were changed in the past day.

- Ansible build jobs (maintained by Ansible Core team)
  - [Stable_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Stable_Ansible/) / [Nightly_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Nightly_Ansible/) - trigger downstream build / install / test jobs
  - [Build_Ansible_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_TAR/)
  - [Build_Ansible_Public_RPM](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_Public_RPM/)
  - [Build_Ansible_DEB](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_DEB/)
- [Ansible_Tower_Integration_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Install/)
- [Ansible_Tower_Integration_Test](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Test/)

## List Of Jenkins Jobs

### Maintained by the Ansible Tower QE team

This is the list of jobs the Ansible Tower QE team maintains.

#### [Pipelines/Backup And Restore](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/backup-and-restore-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/backup-and-restore.groovy) will exercice the Backup and Restore scenario. It takes the following actions:

  * Install Tower
  * Load a dataset
  * Backup the Tower instance
  * Remove and reinstall a fresh Tower instance
  * Restore the dataset
  * Verify the integrity of the dataset

#### [Pipelines/Brew](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/brew-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/brew.groovy) will run the brew related build actions:

  * Build Tower RPM in Brew
  * Build Tower Container in Brew
  * Push the built container in our own registry

#### [Pipelines/Build Artifacts](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/build-artifacts-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/build-artifacts.groovy) will build the miscellaneous artifacts we ship as part of a release:

  * Build Tower Documentation
  * Build Tower Vagrant image
  * Build Tower Amazon AMI

#### [Pipelines/Debian](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/debian-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/debian.groovy) is not meant to be run directly but via the `Pipeline/Release` pipeline.
It defines which Operating System to run the `Pipeline/Dispatch` for. If `latest` is selected as scope, only Ubuntu 16.04 will get selected
while, if `full` is selected and the Tower version supports it, Ubuntu 14.04 would also be selected.

#### [Pipelines/Dispatch](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/dispatch-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/dispatch.groovy) is not meant to be run directly but via the `Pipeline/Release` pipeline.
It defines which Ansible Version to run the `Pipeline/Verification` for based on the supported version of Ansible for a given version of Ansible Tower.

#### [Pipelines/Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/install-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/install.groovy) will run an install of Ansible Tower based on the selected parameters.

#### [Pipelines/Install and Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/integration-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/integration.groovy) will run an install of Ansible Tower based on the selected parameters and run the test suite.

#### [Pipelines/Layered Product Testing](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/lptesting-main-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/lptesting-main.groovy) is used to validate an upcoming version of RHEL to the Interop team.
It is a meta pipeline, it simply, based on the RHEL_COMPOSE_ID, call the proper [Pipelines/Layered Product Testing (permutation)](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/lptesting-pipeline/) jobs. More on Interop Testing available [here](how_to_test_compatibility_with_rhel_prereleases.md).

#### [Pipelines/Layered Product Testing (permutation)](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/lptesting-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/lptesting.groovy) is used to validate an upcoming version of RHEL to the Interop team. It does the following actions:

  * Deploy a RHEL VM on our internal OpenStack
  * Prepare the node to point to the proper repositories
  * Install the specified version of Ansible Tower
  * Run a test

#### [Pipelines/OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/openshift/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/openshift.groovy) is used to validate the health of the OpenShift jobs. It does the following actions:

  * OpenShift Minor Upgrade
  * OpenShift Major Upgrade
  * OpenShift Backup And Restore
  * OpenShift Integration

#### [Pipelines/Red Hat](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/redhat-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/redhat.groovy) is not meant to be run directly but via the `Pipeline/Release` pipeline.
It defines which Operating System to run the `Pipeline/Dispatch` for. If `latest` is selected as scope, only `RHEL 7.latest` will get selected
while, if `full` is selected and the Tower version supports it, `RHEL 7.latest-1` would also be selected.

#### [Pipelines/Release](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/release-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/release.groovy) is meant to verify the health of the release. It  will runthe `Pipeline/Verification` pipeline for all supported OS/Ansible permutation based on the selected `scope`.

#### [Pipelines/Upgrade](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/upgrade-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/upgrade.groovy) will exercice the Upgrade scenario. It takes the following actions:

  * Install Tower
  * Load a dataset
  * Upgrade Tower
  * Verify the integrity of the dataset

#### [Pipelines/Verification](http://jenkins.ansible.eng.rdu2.redhat.com/job/Pipelines/job/verification-pipeline/)

This [pipeline](https://github.com/ansible/tower-qa/blob/devel/tools/jenkins/pipelines/verification.groovy) is meant to verify the health of a given permutation for a release. It will run all needed scenario to validate a release:

  * Minor upgrade (bundle, non-bundle, standalone, cluster)
  * Major upgrade (bundle, non-bundle, standalone, cluster)
  * Backup And Restore (bundle, non-bundle, standalone, cluster)
  * Integration test suite(bundle, non-bundle, standalone, cluster)

#### [qe-issue-bot](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/qe_issue_bot/)

This job aims to send the team a Slack message on the #ship_it channel with current issue status on the various on-going releases.

#### [Test_Tower_E2E_Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E_Pipeline/) - Runs the e2e ui tests

  * Trigger: checks for scm changes against tower/release_X every 2 hours.
  * Build: Builds RPM
  * Deploy: Uses the Ansible Tower Jenkins plugin to deploy a RPM build to GCE
  * Test: Runs the Test_Tower_E2E job against the GCE build
  * Notify: Sends a slack notification to #e2e-resuts and notifies of failure or return-to-success in #ui-talk

#### [Test_Tower_E2E](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E/) - General E2E test execution utility job. Requires a FQDN, username, password
Used as a part of the Test_Tower_E2E_Pipeline
Used after the Openshift Integration runs
Soon: Used post-upgrade pipeline

### Not maintained by the Ansible Tower QE team

This is a list of jobs the Ansible Tower QE team does not maintain per-se but consumes for the aforementionned pipelines.

#### [Build Tower Bundle TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Bundle_TAR/)

Job responsible to build the bundle installer.
**Note**: [Build Tower Dependency Repo](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Dependency_Repo/) should be run first if any dependency has been updated at the errata level.

#### [Build Tower DEB](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_DEB/)

Job responsible to build the Ubuntu apt packages. **Note**: Deprecated starting from `3.6.0`.

#### [Build Tower Dependency Repo](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Dependency_Repo/)

Job responsible to pull the proper dependencies in the [nightly repo](http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/dependencies/).

#### [Build Tower Docs](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Docs/)

Job reponsible to build the Ansible Tower documentation.

#### [Build Tower Image](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Image/)

Job reponsible to build the Ansible Tower Amazon AMI.

#### [Build Tower OpenShift_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_OpenShift_TAR/)

Job reponsible to build the Ansible Tower OpenShift installer.

#### [Build Tower RPM](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_RPM/)

Job responsible to build the Red Hat yum packages.

#### [Build Tower TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_TAR/)

Job reponsible to build the Ansible Tower installer.

#### [Build Tower Vagrant_Box](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Vagrant_Box/)

Job reponsible to build the Ansible Tower Vagrant box.

## YOLO

Yes. You read this title right: Yolo ! What is Yolo ? [Yolo](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Yolo_Express/) (full name: Test_Tower_Yolo_Express), is a pipeline mainly targeted at the Devs and QE side to be able to "compose" a deployment with all the component one needs. One can specify:

  * To deploy Tower or AWX (upstream version of Tower)
  * Tower/AWX fork and branch
  * `ansible/tower-qa` fork and branch
  * `ansible/tower-packaging` fork and branch
  * `ansible/towerkit` fork and branch
  * `ansible/runner` fork and branch


Based on the option selected YOLO can:

  * Build Package
  * Deploy Tower
  * Run Integration Suite
  * Run E2E Suite

**Note**: When refering to YOLO one can hear two terms:

  * **YOLO**: Test suite is run with `yolo or ansible_integration` filter (~300 tests | ~1h20)
  * **SLOWYO**: Test suite is run without filter (~ 3110 tests | ~6h)


## FAQ

* _When is the last time we were testing Tower version X.Y.Z with Ansible version X.Y.Z on OS X version Z and what were the results_

As stated in [Release Verification](#release-verification), current devel and latest-released-version maintenance releases verification process happens nightly, for the oldest version it happens weekly.

The information is available here: http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/releases - at most it would be 1 week old.

* _If I want to trigger a test of Tower version X.Y.Z with Ansible Version X.Y.Z on OS X version Z, how do I do that?_

Use the [YOLO](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/) job if you require a feature branch

* _We don't run full integration on all Ansible versions, right?_

Not during the release verification process. Full integration is run with latest ansible version on each OS. The rest run `-m yolo or ansible_integration`.
The `yolo` mark is a mark we have attempted to apply to get a minimum coverage of each component in Tower. the `ansible_integration` mark as been applied to tests known to expose our sensitive points of contact with breaking changes in Ansible.

* _How do you find results?_

Look a the [dashboard](http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/releases) to find latest results for OS/Ansible version of interest.

* _How do I tell how many times a test has failed in the nightly runs?_

The # in the test results is calculated based on job #’s  -- can be misleading
Example: will say “failing for 25 builds” but actually it is only last night and tonight
Because other jobs happened in between, incrementing the job #’s, but these were not runs from the nightly pipeline
For a more accurate view, look at the particular test and then inspect the history (button on left when in detail view)


* _How can I inspect the health of a current feature in the test results?_

Expand “all test results” and click through the tree. Tests are organized by module and/or folder, each associated with a feature or function.
