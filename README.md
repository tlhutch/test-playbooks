# ansibleworks-qa

The build, test and deployment process for AnsibleWorks (AWX) is managed by [Jenkins](http://50.116.42.103).  This document describes the relevant triggers, jobs and workflow.

## Build Triggers

The following test events are used to trigger [AWX jenkins jobs](http://50.116.42.103/view/AWX/).

### git-push

Any time code changes are pushed into the [ansible-commander.git repository](https://github.com/ansible/ansible-commander), jenkins will trigger the [AWX_Unittest](http://50.116.42.103/view/AWX/job/AWX_Unittest/) job.

### git-tag

Jenkins regularly monitors the [ansible-commander.git repository](https://github.com/ansible/ansible-commander) for the presence of [new tags](https://github.com/ansible/ansible-commander/releases).  If a new git-tag is deteced, the production build process is triggered.  The job used to detect the presence of new git-tags is [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks%20Release%20Tag%20Scan/).

### cron

On a daily interval, jenkins will trigger the development build process with the job [Nightly_Build - AWX](http://50.116.42.103/view/AWX/job/Nightly%20Build%20-%20AWX/).

### manual

All jenkins jobs can be triggered manually.  Jenkins will prompt for any required build parameters.

## Build Workflow

There are two primary workflows through the AWX build process:
 1. Release (`OFFICIAL=yes`) - builds `.rpm`, `.deb` and `.tgz` files for official product releases
 1. Nightly (`OFFICIAL=no`) - builds `.rpm`, `.deb` and `.tgz` files for internal purposes, and initiates tests

### Release

The official build workflow is triggered by the job [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks%20Release%20Tag%20Scan/).  All jobs in this workflow use the parameter `OFFICIAL=yes`.  Build artifacts (e.g. `.rpm`, `.deb` and `.tgz` files) are intended for production-use.

* [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks%20Release%20Tag%20Scan/)
  * [AWX_Build_Setup_TAR](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20Setup%20TAR/)
  * [AWX_Build_RPM](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20RPM/)
  * [AWX_Build_DEB](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20DEB/)

### Nightly

The nightly build workflow is triggered on a ... wait for it ... nightly basis by jenkins.  All jobs use the parameter `OFFICIAL=no`.  Build artifacts (e.g. `.rpm`, `.deb` and `.tgz` files) are intended for internal testing purposes only.

* [Nightly_Build - AWX](http://50.116.42.103/view/AWX/job/Nightly%20Build%20-%20AWX/)
  * [AWX_Build_Setup_TAR](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20Setup%20TAR/)
  * [AWX_Build_RPM](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20RPM/)
    * [AWX_Nightly_Install](http://50.116.42.103/view/AWX/job/AWX_Nightly_Install) (for rpm-based distros only)
      * [AWX_Integration_Test](http://50.116.42.103/view/AWX/job/AWX_Integration_Test) (for rpm-based distros only)
  * [AWX_Build_DEB](http://50.116.42.103/view/AWX/job/Build%20AnsibleWorks%20DEB/)
    * [AWX_Nightly_Install](http://50.116.42.103/view/AWX/job/AWX_Nightly_Install) (for ubuntu only)
      * [AWX_Integration_Test](http://50.116.42.103/view/AWX/job/AWX_Integration_Test) (for ubuntu only)

