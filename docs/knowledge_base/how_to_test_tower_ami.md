# How to test the Tower AMI

## Building an AMI

In order to build an AMI, you must first build the Tower TAR and RPM artifacts, then the image itself can be created. When running any build job, pay particular attention to the following parameters:

* Branch parameters - these should point to the specific release branch (which generally takes the form `origin/release_x.y.z`)
* TRIGGER - this should be disabled to avoid triggering downstream jobs (installs / tests)
* Staging / Official - should be `no`

For all other parameters, the defaults can safely be used.

Note that if the nightly pipeline (triggered by Nightly_Tower or Nightly_Tower_Patch) has run recently, this will trigger the above jobs. In this case, an AMI should already be available.

Building the tower TAR, RPM, and AMI requires different jobs for different releases:

### 3.1.x

* Open http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/_Legacy_Tower_Jobs/
* Build Build_Tower_TAR_Old_Repo, Build_Tower_RPM_Old_Repo, and Build_Tower_Image_Old_Repo (in that order)

### 3.2.x or later

* Open http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/
* Build Build_Tower_TAR, Build_Tower_RPM, and Build_Tower_Image (in that order)

## Deploying an AMI (manually)

It can sometimes be helpful to locate resources in EC2's UI. The following steps show how to deploy a Tower AMI using Amazon's AMI deployment wizard.

### Locating the AMI

* Open https://aworks.signin.aws.amazon.com and sign in.
* Select the EC2 service.
* In the top-right corner, be sure that the N. Virginia datacenter is selected.
* On the navigation menu at left, under the IMAGES section, click on AMIs.
* In the search bar, enter the release number (e.g. 3.1.8). This should return an image with a name similar to Ansible Tower 3.1.8 - 0.

### Launching an Image
* Right-click on the image found in the previous section, and select Launch.
* Select m4.large for Type and click Next: Configure Instance Details.
* For Network, select qe-vpc. Set Auto-assign Public IP to Enable. Click Next: Add Storage.
* Change size to 20 GiB. Click Next: Add Tags.
* Click Add Tag. Under Key, enter Name. Under Value, enter a name for the AMI (e.g. jladd-tower-318-ami). Click Next: Configure Security Group.
* Select Select an existing security group. Select Tower Cluster in QE VPC.
* Click Review and Launch. Click Launch.
* Use an existing key to which you have access or provide a new key. Click Launch Instances.

### Accessing the Tower Instance
* Picking up from the last section, click View Instances.
* Enter the name of your instance in the search field.
* Click on the row where your instance is shown. In the section at bottom, on the Description tab, find the Public DNS (IPv4) field. Copy the FQDN of the instance.
* Open a terminal and run `ssh centos@ec2-18-212-118-178.compute-1.amazonaws.com`
* The message of the day should show a Username and Password.
* Point a browser to your instance's FQDN. If your browser shows a security alert (due to a self-signed certificate used by tower), confirm the warning and choose to proceed opening the page.
* Enter the username / password copied earlier to log in.

## Deploying an AMI (using a playbook)

First, you will need to find the AMI ID that you wish to deploy. (By default, the playbook deploys the latest image).
* Open https://aworks.signin.aws.amazon.com and sign in.
* Select the EC2 service.
* In the top-right corner, be sure that the N. Virginia datacenter is selected.
* On the navigation menu at left, under the IMAGES section, click on AMIs.
* In the search bar, enter the release number (e.g. 3.1.8). This should return an image with a name similar to Ansible Tower 3.1.8 - 0. Click on the row listing this image.
* The bottom of the page should show detailed information about the image. Copy the AMI ID. (It should look similar to `ami-32e0fd4d`).

Next, prepare the prequisites for deploying the image:
* Clone https://github.com/ansible/tower-qa
* Build a virtualenv for the tower-qa repo (using its requirements.txt file)
* Activate the virtualenv
* Ensure that ansible is installed
* Your BASH profile should source an amazon access key and key id:
```
export AWS_SECRET_ACCESS_KEY=...
export AWS_ACCESS_KEY_ID=...
```
(see https://aws.amazon.com/blogs/security/wheres-my-secret-access-key/ if you need to create a new key)

Finally, run the playbook:
* In the root folder, run `ansible-playbook -i playbooks/inventory -e tower_ami_id=<INSERT-ID-HERE> playbooks/deploy-tower-ami.yml`, substituting in the value of the AMI ID found earlier.
* After the playbook run finishes, the FQDN of the deployed instance will be listed in the summary details of the run. Point your browser to this address.
* The playbook configures the tower instance to use the following login credentials - `admin` / `ch@m3m3`. Use this to log into tower.

## Performing a sanity check

As a basic test of tower services, confirm that you can run the Demo Job Template successfully.

# Reference Information

The Ansible Tower Installation and Reference Guide provides information on how users can download, deploy, and log into an AMI (or vagrant) image:

https://docs.ansible.com/ansible-tower/latest/html/installandreference/tower_installer.html#obtaining-the-tower-installation-program

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Aug 3, 2018.
