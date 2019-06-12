### Getting Started

Welcome to `tower-qa`! Herein lies our beloved API integration tests, playbooks, and scripts.

##### Getting Started with API Tests
Clone the `tower-qa` repo with:
```
$ git clone git@github.com:ansible/tower-qa.git tower-qa
```

If you will be running tests or using tower's client utility, `tkit`, against multple versions of tower, you may want to create a `tower-qa` checkout for each branch:
```
$ git clone git@github.com:ansible/tower-qa.git tower-qa-(branch_name)
$ cd tower-qa-(branch_name)
$ git checkout (branch_name)
```
where `branch_name` is `master`, `release_3.2`, `release_3.1`, etc.

We recommend using virtual environments to manage dependencies:
* [virtualenv](https://virtualenv.pypa.io/en/stable/installation/)
* [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/install.html)

After installing virtualenv and virtualenvwrapper, you can create a virtualenv with:
```
$ mkvirtualenv tower-qa
(tower-qa) $ pip install -U -r requirements.txt
```

If you have different `tower-qa` checkouts, you should create a different virtualenv for each checkout. Note that different versions of `tower-qa` often have different dependencies!

To run tests:
* You will need to decrypt `config/credentials.vault`. For vault password, ask a QE member.
```
$ ansible-vault decrypt --ask-vault-pass --output=config/credentials.yml config/credentials.vault
```
* If running tests against Tower running in Docker, You will need to create a superuser in `tools_tower_1` with username "admin" and password "fo0m4nchU":
```
$ docker exec -it tools_awx_1 bash

$ awx-manage createsuperuser
$ awx-manage create_preload_data
```
* The Docker environment also requires cloning the license writer inside `tools_tower_1`:
```
$ git clone https://github.com/ansible/tower-license

$ cd tower-license
$ . /venv/awx/bin/activate
$ pip install .
```

Run tests against Tower in Docker with:
```
$ py.test --ansible-host-pattern=127.0.0.1 --base-url http://127.0.0.1:8013 --api-credentials=config/credentials.yml --ansible-sudo --pdb -vs -k test_labels.py
```
* If the test fails, it will drop into a `pdb` session with `--pdb`.
* `-vs` will give you a REST log.
* `-k` determines which tests will run.

Run tests with four processes to increase speed:
```
$ py.test --ansible-host-pattern=127.0.0.1 --base-url http://127.0.0.1:8013 --api-credentials=config/credentials.yml --ansible-sudo -vs --mp --np 4 -k test_labels.py
```

##### Getting Started with Playbooks
* The "deploy" playbooks deploy Tower in various configurations (with LDAP, with cluster, via bundle installer etc.).
* The "images" files provide extra variables needed for certain playbooks to run.

It may be helpful to create a `vars.yml` file to house additional ansible variables:
```
---
delete_on_start: true
create_ec2_wait_upon_creation: false
terminate_ec2_wait_upon_creation: false

ec2_key_name: 'cwang'  # UPDATE ME
ec2_public_key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
instance_name_prefix: 'cwang'  # UPDATE ME

user_data_install_py2: &install_py2
  "{{ lookup('file', 'files/install_py2.sh') }}"

# ansible_nightly_repo: 'http://nightlies.testing.ansible.com/ansible_nightlies_QcGXFZKv5VfQHi/stable-2.4'
# ansible_install_method: 'nightly'

# aw_repo_url: 'http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/release_3.2.3'
aw_repo_url: 'http://releases.ansible.com/ansible-tower'
awx_setup_path: 'setup/ansible-tower-setup-latest.tar.gz'
# awx_setup_path: 'setup/ansible-tower-setup-3.2.1.tar.gz'
awx_upgrade: false

minimum_var_space: 0
gpgcheck: 0
pendo_state: 'off'

cluster_install: false

admin_password: fo0m4nchU
pg_password: fo0m4nchU
rds_username: 'tower'
rds_password: 'fo0m4nchU'
```

The Ansible ec2 inventory script needs the following environment variables:
```
    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'
```
* If you need credentials, ask [Graham Mainwarning](mailto:gmainwar@redhat.com).

Invoke playbook with:
```
(tower-qa) ~/git/tower-qa/playbooks$ ansible-playbook -i inventory deploy-tower.yml -e @images-ec2.yml -e @vars.yml
```

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) May 10, 2018.
