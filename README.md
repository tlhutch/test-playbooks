# ansibleworks-qa

This repository is a landing place for ansibleworks testing.  At present, it's not well organized.

## Build Triggers

The following test events are used to trigger jenkins jobs.

### git-push

Any time code changes are pushed into the git repository, jenkins will trigger the [AWX_Unittest](http://50.116.42.103/view/AWX/job/AWX_Unittest/) job.


### git-tag

Jenkins regularly monitors the awx git repository for the presence of new tags.  If a new git-tag is deteced, the production build process is triggered.  The job used to detect the presence of new git-tags is [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks_Release_Tag_Scan/)

### cron

On a daily interval, jenkins will trigger the development build process with the job [Nightly_Build - AWX](http://50.116.42.103/view/AWX/job/Nightly%20Build%20-%20AWX/).

### manual

All jenkins jobs can be triggered manually.  Jenkins will prompt you for any required build parameters.

## Nightly Build Workflow

The nightly build workflow is triggered on a ... wait for it ... nightly basis by jenkins.  All jobs use the parameter `OFFICIAL=no`.  Builds are intended for internal use only.

* [Nightly_Build - AWX](http://50.116.42.103/view/AWX/job/Nightly%20Build%20-%20AWX/)
  * [AWX_Build_Setup_TAR]((http://50.116.42.103/view/AWX/job/AWX_Build_Setup_TAR)
  * [AWX_Build_RPM]((http://50.116.42.103/view/AWX/job/AWX_Build_RPM)
    * [AWX_Nightly_Install]((http://50.116.42.103/view/AWX/job/AWX_Nightly_Install)  (for rpm-based distros only)
      * [AWX_Integration_Test](http://50.116.42.103/view/AWX/job/AWX_Integration_Test) (for rpm-based distros only)
  * [AWX_Build_DEB]((http://50.116.42.103/view/AWX/job/AWX_Build_DEB)
    * [AWX_Nightly_Install]((http://50.116.42.103/view/AWX/job/AWX_Nightly_Install)  (for ubuntu only)
      * [AWX_Integration_Test](http://50.116.42.103/view/AWX/job/AWX_Integration_Test) (for ubuntu only)

ASCII-version

    Nightly_Build - AWX
    |
    +--> AWX_Build_Setup_TAR
    |
    +--> AWX_Build_RPM
    |    |
    |    +--> AWX_Nightly_Install (PLATFORM=rhel-6.4-x86_64, PROVIDER=rax)
    |    |    |
    |    |    +--> AWX_Integration_Test (PLATFORM=rhel-6.4-x86_64, PROVIDER=rax)
    |    |
    |    +--> AWX_Nightly_Install (PLATFORM=centos-6.4-x86_64, PROVIDER=rax)
    |    |    |
    |    |    +--> AWX_Integration_Test (PLATFORM=centos-6.4-x86_64, PROVIDER=rax)
    |    |
    |    +--> AWX_Nightly_Install (PLATFORM=rhel-6.4-x86_64, PROVIDER=ec2)
    |    |    |
    |    |    +--> AWX_Integration_Test (PLATFORM=rhel-6.4-x86_64, PROVIDER=ec2)
    |    |
    |    +--> AWX_Nightly_Install (PLATFORM=centos-6.4-x86_64, PROVIDER=ec2)
    |         |
    |         +--> AWX_Integration_Test (PLATFORM=centos-6.4-x86_64, PROVIDER=ec2)
    |
    +--> AWX_Build_DEB
         |
         +--> AWX_Nightly_Install (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=rax)
         |    |
         |    +--> AWX_Integration_Test (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=rax)
         |
         +--> AWX_Nightly_Install (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=ec2)
              |
              +--> AWX_Integration_Test (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=ec2)


    Nightly_Build - AWX
    |
    +--> AWX_Build_Setup_TAR
    |
    +--> AWX_Build_RPM
    |    |
    |    |   +--------------------------------------------------------------+
    |    |   |AWX_Nightly_Install (PLATFORM=rhel-6.4-x86_64, PROVIDER=ec2)  |
    |    |   |AWX_Nightly_Install (PLATFORM=rhel-6.4-x86_64, PROVIDER=rax)  |
    |    +-->|AWX_Nightly_Install (PLATFORM=centos-6.4-x86_64, PROVIDER=ec2)|
    |        |AWX_Nightly_Install (PLATFORM=centos-6.4-x86_64, PROVIDER=rax)|
    |        +--------------------------------------------------------------+
    |         |
    |         |   +---------------------------------------------------------------+
    |         |   |AWX_Integration_Test (PLATFORM=rhel-6.4-x86_64, PROVIDER=ec2)  |
    |         |   |AWX_Integration_Test (PLATFORM=rhel-6.4-x86_64, PROVIDER=rax)  |
    |         +-->|AWX_Integration_Test (PLATFORM=centos-6.4-x86_64, PROVIDER=ec2)|
    |             |AWX_Integration_Test (PLATFORM=centos-6.4-x86_64, PROVIDER=rax)|
    |             +---------------------------------------------------------------+
    |
    +--> AWX_Build_DEB
         |
         |   +-----------------------------------------------------------------+
         |   |AWX_Nightly_Install (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=rax) |
         +-->|AWX_Nightly_Install (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=ec2) |
             +-----------------------------------------------------------------+
              |
              |   +------------------------------------------------------------------+
              |   |AWX_Integration_Test (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=rax) |
              +-->|AWX_Integration_Test (PLATFORM=ubuntu-12.04-x86_64, PROVIDER=ec2) |
                  +------------------------------------------------------------------+

## Official Build Workflow

The official build workflow is triggered by the job [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks_Release_Tag_Scan/).  All jobs use the parameter `OFFICIAL=yes`.  Builds are intended for production-use.

* [AnsibleWorks_Release_Tag_Scan](http://50.116.42.103/view/AWX/job/AnsibleWorks_Release_Tag_Scan/)
  * [AWX_Build_Setup_TAR]((http://50.116.42.103/view/AWX/job/AWX_Build_Setup_TAR)
  * [AWX_Build_RPM]((http://50.116.42.103/view/AWX/job/AWX_Build_RPM)
  * [AWX_Build_DEB]((http://50.116.42.103/view/AWX/job/AWX_Build_DEB)

ASCII-version

    AnsibleWorks_Release_Tag_Scan
    |
    +--> AWX_Build_Setup_TAR
    |
    +--> AWX_Build_RPM
    |
    +--> AWX_Build_DEB
