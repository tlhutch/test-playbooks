# How to test the Tower VirtualBox image

## Building a VirtualBox image

In order to build a VirtualBox image, you must first build the Tower TAR and RPM artifacts, then the image itself can be created. When running any build job, pay particular attention to the following parameters:

* Branch parameters - these should point to the specific release branch (which generally takes the form `origin/release_x.y.z`)
* TRIGGER - this should be disabled to avoid triggering downstream jobs (installs / tests)
* Staging / Official - should be `no`

For all other parameters, the defaults can safely be used.

Note that the nightly pipeline (triggered by Nightly_Tower or Nightly_Tower_Patch) triggers the TAR and RPM build jobs but _will not_ currently trigger the VirtualBox image build.

Building the tower TAR and RPM artifacts requires different jobs for different releases:

### 3.1.x

* Open http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/_Legacy_Tower_Jobs/
* Build Build_Tower_TAR_Old_Repo and Build_Tower_RPM_Old_Repo

### 3.2.x or later

* Open http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/
* Build Build_Tower_TAR and Build_Tower_RPM

After the TAR and RPM artifacts have been built, build [Build_Tower_Vagrant_Box](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Vagrant_Box/). Remember to set `TOWER_BRANCH` to the desired branch (e.g. `origin/release_3.2.6`).

## Deploying the VirtualBox image

The Ansible Tower Quick Installation Guide currently [recommends using Vagrant](https://docs.ansible.com/ansible-tower/latest/html/quickinstall/download_tower.html#vagrant) to deploy the VirtualBox image. Download and install [Vagrant](https://www.vagrantup.com/intro/getting-started/install.html) and [VirtualBox](https://www.virtualbox.org/).

After Vagrant has been installed:

* Download the VirtualBox artifact from the [Build_Tower_Vagrant_Box](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Build_Tower_Vagrant_Box/) job (e.g. ansible-tower-3.2.6-virtualbox.box)
* `vagrant box add tower-x.y.z /path/to/ansible-tower-x.y.z-virtualbox.box`
* `mkdir ~/Vagrant/tower; cd ~/Vagrant/tower`
* `vagrant init tower-x.y.z`
* `vagrant up`
* `vagrant ssh`
* Use the URL and admin password listed in the message of the day to log in to tower

## Performing a sanity check

As a basic test of tower services, confirm that you can run the Demo Job Template successfully.

## Cleaning up deployed vm

* `cd ~/Vagrant/tower`
* `vagrant halt`
* `vagrant destroy`

## Checking status of deployed vm

If you are unsure what state the deployed vm is in, the following command shows the state of all Vagrant images:

* `vagrant global-status`

# Reference Information

The [Ansible Tower Quick Installation Guide](https://docs.ansible.com/ansible-tower/latest/html/quickinstall/download_tower.html#vagrant) provides information on how users can download, deploy and log into the latest VirtualBox image. Note that following the steps provided in the user documentation will deploy the latest _released_ VirtualBox image. The instructions on this page show how to deploy any image built in Jenkins.

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Aug 8, 2018.
