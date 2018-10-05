# How to test compatibility with RHEL pre-releases

## Overview

When RHEL approaches the end of a release, it will cut an alpha and beta image. When each image is available, an e-mail is sent out to other Red Hat product groups, prompting the groups to pull the RHEL image, install their product on the platform, and confirm their product remains functional on the new platform. In general, interoperability testing with the alpha image is optional, while testing against the beta image is mandatory.

## Prerequisites

* These instructions assume that you have a working knowledge of towerkit (the QE team's Python client for Tower) and tower-qa (the QE team's collection of playbooks and tests for Tower).
* You will need an account on access.redhat.com registered to your redhat.com e-mail address. Your account will need to have active RHEL subscriptions associated with this. Red Hatters should be granted access to these subscriptions automatically. For more information on access.redhat.com and RHEL subscriptions, see the "Registering with access.redhat.com" section below.

## Determining which versions of Tower to test

* The RHEL pre-release image should be tested with each [currently supported version of Tower](https://access.redhat.com/support/policy/updates/ansible-tower).

## Getting tower-qa

Follow the steps in QE's [Getting Started Guide](docs/knowledge_base/getting_started.md#getting-started) to clone the tower-qa repo and create a virtualenv. Be sure to do this for each branch of tower-qa associated with a currently supported version of Tower. (Note that you will not need to follow any steps in the Getting Started Guide related to setting up / configuring Tower using Docker).

## Downloading the RHEL image

* Connect to the Red Hat VPN
* Open http://download-node-02.eng.bos.redhat.com/rel-eng/
* Find the folder corresponding to the current release (e.g. RHEL-7.6-Beta-1.2)
* Open http://download-node-02.eng.bos.redhat.com/rel-eng/CURRENT_RELEASE/compose/Server/x86_64/iso
* Click on the `*dvd1.iso` file to begin the download. (e.g. http://download-node-02.eng.bos.redhat.com/rel-eng/RHEL-7.6-Beta-1.2/compose/Server/x86_64/iso/RHEL-7.6-20180814.0-Server-x86_64-dvd1.iso). Note that the download can take a while. You may want to do the download from Firefox which supports resuming downloads.

## Creating a new VM in VirtualBox

* Download [VirtualBox](https://www.virtualbox.org/wiki/Downloads). Open VirtualBox.
* Click on the New icon at top
* Enter a name for the instance (e.g. rhel-7.6-Beta-1.2). Set Type to Linux. Set Version to Red Hat (64-bit). Click Continue
* Set memory to at least 2GB.
* Choose to Create a virtual hard disk now.
* Accept the default image type (VDI).
* Choose to have the virtual hard disk file Dynamically allocated.
* Set the disk size to 20 GB (you can probably be more conservative than this if you want)
* Click Create

## Configuring VM to boot from RHEL CD

* Find your VM listed in VirtualBox. Click on the VM, then click on the Settings icon at top.
* Click on the Storage icon.
* Under Controller: IDE, click on the cd (titled 'Empty'). On the right-hand side, under the Attributes section, click on the cd image. Select Choose Virtual Optical Disk File... and select the `*.iso` image downloaded earlier. Click Open.
* Click OK to exit the VM settings page.

## Installing RHEL

* Find your VM listed in VirtualBox. Click on the VM, then click on Start.
* The VM should begin booting from the RHEL installation disk. Skip the integrity check at the beginning.
* Set English as the language to use during installation.
* On the Installation Summary page, click on Software Selection. Under Base Environment select Minimal Install. Under Add-Ons for Selected Environment, select Development Tools and System Administration Tools. Click Done.
* Click on Installation Destination. Without making any changes, click Done to accept the default partitioning scheme.
* **Click on Network & Host Name. In the top-right corner, switch the toggle to On.** Click Done.
* Optionally click on Date & Time to update the timezone if you are not located in the Eastern Timezone.
* Click Begin Installation.
* While the installation is in progress, click on Root Password. Set the password.
* Click on User Creation. Enter a user name and password. Select Make this user administrator. Click Done.
* The installation may only take about five minutes. When it is finished, click Reboot.

## Enabling port forwarding, adding public key to VM

* Find your VM listed in VirtualBox. Click on the VM, then click Settings.
* Click on the Network icon.
* Confirm NAT is selected.
* Click on Advanced. Click on Port Forwarding.
* Click the plus icon to add a new rule. In the rule, set Host Port to 2222 and Guest Port to 22. All other fields can be left as is.
* Click the plus icon to add a second rule. In the rule, set Host Port to 4444 and Guest Port to 443. All other fields can be left as is. Click Okay.
* Click OK to exit the Settings window.
* On the host machine, run `ifconfig`. Look for a new ip address that is on your current network. Test connecting to the VM using this address - for example, `ssh -p 2222 jim@192.168.1.5`. Enter the user's password when prompted. Repeat this process with other addresses as necessary until you have confirmed which address belongs to your VM.
* Use `ssh-copy-id` to add your public key to the VM - for example, `ssh-copy-id -i ~/.ssh/id_rsa.pub jim@192.168.1.5`.
* Confirm that you can now log in to the VM without using a password.
* Use `ssh-copy-id` to add your key for the root user as well.

## Registering with access.redhat.com

* Note: It can take access.redhat.com a few minutes to load sometimes, especially on the page listing subscriptions available to a user. Be patient, though, and the pages will eventually load. : /
* Visit access.redhat.com and register using your redhat.com e-mail address
* After registering, confirm that RHEL subscriptions are associated with your account by visiting access.redhat.com, clicking on My Subscriptions (towards the bottom), and clicking Inventory (just beneath the Subscription Utilization link). Search for Red Hat Enterprise Linux. Several subscriptions should be listed (e.g. Red Hat Enterprise Linux Developer Suite).

## Registering system using subscription-manager

* ssh to the VM
* Run `sudo subscription-manager register`. When prompted, provide your username (i.e. access.redhat.com e-mail address) and password.
* Run `sudo subscription-manager attach`. You may need to wait a minute or two for the command to complete. When it does, it should show something similar to:

```
Installed Product Current Status:
Product Name: Red Hat Enterprise Linux Server
Status:       Subscribed
```

## Creating a repo file to point to pre-release packages

* Log in to the VM and switch to the root account
* cd /etc/yum.repos.d
* Confirm that only one file is present, `redhat.repo`. This file points to repos which contain pre-release packages. The server listed is not accessible, though, even on the RH VPN. Delete this file.
* Create a new file, called rhel-7-server-prerelease.repo, with the following contents (updating the baseurl to the release folder located in "Downloading the RHEL image" - in the example below, this is `RHEL-7.6-Beta-1.2`):
```
[rhel-7-server-prerelease]
baseurl = http://download-node-02.eng.bos.redhat.com/rel-eng/RHEL-7.6-Beta-1.2/compose/Server/x86_64/os
sslverify = 0
name = RHEL Pre-release Packages
enabled = 1
gpgcheck = 0
```
* Run `yum clean all` to clear yum's cache

## Taking a snapshot of the VM

Save the current state of the VM so that the VM can be reverted in between Tower installations.

* Find your VM listed in VirtualBox. Right-click on the VM, select Close -> Power Off. Alternatively, if you have an active ssh session, you can run `shutdown -h now`
* With the VM still selected, click the Machine Tools icon (top-right) and select Snapshots
* Click the Take icon. Give the snapshot a name (e.g. Fresh install)

## Confirming which versions of Ansible are compatible with Tower

Before installing Tower (especially older versions of Tower), log in to access.redhat.com, then check the [Ansible / Tower support matrix](https://access.redhat.com/articles/3382771) to see which versions of Ansible are supported for a given version of Tower. You will need to make sure that the correct version of Ansible is used in the following section. (This will be specified using the `awx_setup_path` extravar passed to the `install-tower.yml` playbook).

## Installing Tower
* Power on the VM (Note that in between reboots the VM's IP address may change. Re-run `ifconfig` on the host to search for a new address if you are unable to connect to the VM.
* Activate the virtualenv for the tower-qa branch that corresponds to the version of tower you will be deploying (`master`, `release_3.2`, `release_3.1`, etc)
* cd to your `tower-qa` checkout, create `playbooks/inventory-rhel-prelease` and provide connection information for your VM:
```
[tower]
192.168.1.5 ansible_user=root ansible_port=2222
```
* Run the following to install Tower on the vm (updating the `aw_repo_url` and `ansible_nightly_repo` to point to the correct branch of tower and ansible, respectively. Also set `admin_password` and `pg_password`. If you are unsure what to use for any of these fields, get in touch with a member of the Tower QE team):
```
ansible-playbook -i playbooks/inventory -e @playbooks/inventory-virtualbox -e out_of_box_os=True -e minimum_var_space=0 -e gpgcheck=0 -e pendo_state=off -e ansible_nightly_repo=http://ansible.nightlies.url/path/to/release -e aw_repo_url=http://tower.nightlies.url/path/to/release -e awx_setup_path=/setup/ansible-tower-setup-latest.tar.gz -e ansible_install_method=nightly -e admin_password='CHANGEME' -e pg_password='CHANGEME' playbooks/install-tower.yml
```
* Confirm that you can access the Tower UI (e.g. https://192.168.1.5:4444) and Tower API (e.g. https://192.168.1.5:4444/api/v2/). Make sure that you set `https` as the protocol when accessing tower's UI / API.

## Running a smoke test

* Activate the virtualenv corresponding to the version of Tower that you are testing.
* Run `tkit -t https://192.168.1.5:4444 -l` (substituting in the correct address for your VM)
* Run the following script to do a basic smoke test of tower:
```
jt = v2.job_templates.create()
jt.ds.inventory.add_host()
job = jt.launch().wait_until_completed()
print(job.is_successful)
```
* After confirming that the above returns `True`, open the Tower UI, navigate to the jobs page and check the job details page for the job that just completed to make sure that the Tower UI is rendering correctly.

## Reverting VM / Installing other versions of Tower

* After completing the above steps for one version of Tower, revert the VM image in VirtualBox to the snapshot taken earlier.
* Locate the next release to test in the [Tower lifecycle page](https://access.redhat.com/support/policy/updates/ansible-tower). Switch to the `tower-qa` checkout and corresponding virtualenv for this release.
* Repeat the steps for installing / testing Tower. When running the `ansible-playbook` command to run the Tower installation, be sure to update the `aw_repo_url` to the correct release URL. For help locating the URL for past / current releases, get in touch with a member of the Tower QE team.

## Running Tower installs in parallel

Like other hypervisors, VirtualBox supports cloning VMs. By cloning the base RHEL install, you can run different tower installations on the same host in parallel.

* In VirtualBox, select your VM. Click on Machine Tools -> Snapshots. Select your snapshot and click the Clone icon.
* Give the cloned VM a name and select Reinitialize the MAC address of all network cards. Click Continue.
* Select the cloned VM. Edit the port forwarding settings (which were also copied from the original vm). In the first rule, change 2222 to 2223. In the second rule, change 4444 to 4445. To ssh to the original vm, you would still use port 2222. To ssh to your cloned VM, use port 2223. Use the same IP address in both cases. (Network Address Translation is what allows you to connect to different VMs by changing the port alone). Similarly, to access the original Tower webserver you should still use port 4444. To access the Tower webserver for the cloned instance use port 4445.

## Signing off on the pre-release RHEL image

* After all Tower installs pass, visit the Vault page requesting sign-offs (the sign-off page for RHEL 7.6 Beta looked like [this](https://vault.engineering.redhat.com/showRequest?requestid=2879)), scroll to the bottom of the page, add a comment like the one below and click Sign Off.
```
The Ansible Tower QE team has confirmed that all supported versions of Tower can be installed on RHEL 7.6 Beta 1.2. The following versions of Tower were tested:

* Tower 3.3.0 (currently in development)
* Tower 3.2.6
* Tower 3.1.8
```

# Reference
* RHEL Layered Product Interoperability Testing Information Session - ([Slides](https://docs.google.com/presentation/d/14T38IbMMMC6JBBbhKcFf7RXTu7xT2mBPZeQ7NM34rZg/edit#slide=id.gb6f3e2d2d_2_207)) ([Recording](https://bluejeans.com/s/DhW@w))
* [RHEL 6, 7, 8 Interoperability testing spreadsheet (Test Status)](https://docs.google.com/spreadsheets/d/1nLRLxubSlctsyVIlkW6Kbob0kSqQYDNxbbx30rwg82w/edit#gid=1416156808)
* [RHEL 8.0 Interop Dashboard (Confluence)](https://docs.engineering.redhat.com/display/PIT/RHEL+8.0+Interop+Dashboard)
* [RHEL Layered Product Interoperability Testing (Confluence)](https://docs.engineering.redhat.com/display/PIT/RHEL+Layered+Product+Interoperability+Testing)
* [QE Product Interop Testing Group (Mojo)](https://mojo.redhat.com/groups/qe-product-interop-testing)

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Oct 5, 2018.
