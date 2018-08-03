# How to run integrated tests for 3.1 traditional cluster

## Background

* In the 3.1 timeframe, the Tower QE team did not have a Jenkins job for deploying Tower or running integrated tests.
* We did, however, have a playbook ([deploy-tower-ha.yml](https://github.com/ansible/tower-qa/blob/release_3.1/playbooks/deploy-tower-ha.yml)) for deploying a cluster with three nodes (see [images-ha.yml](https://github.com/ansible/tower-qa/blob/release_3.1/playbooks/images-ha.yml) for cluster topology).
* The tests ran against the 3.1 traditional cluster during release testing are listed in the [3.1.0 Test Plan](https://github.com/ansible/tower-qa/blob/release_3.1/docs/test_plans/testplan-3.1.0.md#clusteringha-ryan).
* These tests primarily focus on:
   - installing various topologies
   - provisioning / deprovisioning nodes using setup.sh
   - load balancing jobs
   - benchmarking and stress testing

The rest of the document describes how to deploy and (manually) test a 3.1.x Tower cluster.

## Install the cluster

First, prepare an environment by:
* Cloning the https://github.com/ansible/tower-qa repo and checking out branch `release_3.1`.
* Creating a new virtualenv and installing the packages listed in requirements.txt
* Installing Ansible
* Sourcing the virtualenv, and
* Sourcing AWS access key information in you BASH profile:
```
export AWS_SECRET_ACCESS_KEY=...
export AWS_ACCESS_KEY_ID=...
```
(see https://aws.amazon.com/blogs/security/wheres-my-secret-access-key/ if you need to create a new AWS key)

Next, run the following command to install the cluster:
```bash
ansible-playbook -i playbooks/inventory -e @playbooks/images-ha.yml \
                 -e minimum_var_space=0 -e gpgcheck=0 -e pendo_state=off \
                 -e ansible_nightly_repo=http://nightlies.testing.ansible.com/ansible_nightlies_QcGXFZKv5VfQHi/stable-2.4 \
                 -e aw_repo_url=http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/release_3.1.8 \
                 -e awx_setup_path=/setup/ansible-tower-setup-latest.tar.gz \
                 -e ansible_install_method=nightly \
                 -e admin_password='CHANGEME' -e pg_password='CHANGEME' \
                 playbooks/deploy-tower-ha.yml
```

* Update `ansible_nightly_repo` if another version of ansible is needed. (https://access.redhat.com/articles/3382771 provides a list of supported versions of Ansible for each version of Tower. Note that you need to be logged into access.redhat.com in order for the entire matrix to be displayed, otherwise only a few cells will be populated).
* Update aw_repo_url to point to the current 3.1.* release of Tower
* Add `-e instance_name_prefix=<your instance name>` if you would like to specify a prefix that should be used when naming instances in EC2

The installation takes about 30 minutes. When the playbook finishes, the playbook summary will list the instances in your cluster. The instance that ran the most tasks is the instance from which the Tower install was run. You can use the FQDN listed for this instance to access your Tower cluster.

## Run through (manual) integrated tests

The tests ran against the 3.1 traditional cluster are listed in the [3.1.0 Test Plan](https://github.com/ansible/tower-qa/blob/release_3.1/docs/test_plans/testplan-3.1.0.md#clusteringha-ryan). Again, these tests emphasize:
- installing various topologies
- provisioning / deprovisioning nodes using setup.sh
- load balancing jobs
- benchmarking and stress testing

Any of these scenarios can be re-executed depending on what changes took place in the upcoming 3.1.x release.

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Aug 3, 2018.
