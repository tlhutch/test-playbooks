### How to Verify Backup-Restore in OpenShift

We informally support two configurations with Tower in OpenShift and we will need to test both. These are:
* Database pod housed in OpenShift as part of the Tower deployment.
* Database external to our OpenShift cluster.

To setup Tower with an internal postgres pod, see what our `Test_Tower_OpenShift_Deploy` Jenkins job does. Or just do:
* Download the OpenShift installer package and unpack.
* Create a `vars.yml` file:
```
---
tower_package_version: 3.3.0.1123  # needs update
openshift_host: https://console.openshift.ansible.eng.rdu2.redhat.com:8443
openshift_project: tower-qe
openshift_user: jenkins
openshift_skip_tls_verify: true
default_admin_password: fo0m4nchU
openshift_pg_emptydir: yes
```
* Install with:
```
./setup_openshift.sh -e @vars.yml -e openshift_password=your_password
```
* Create some resources in Tower (an organization).
* Create a backup of Tower:
```
./setup_openshift -b -e @vars.yml -e openshift_password=your_password
```
* Delete your resources and your inventory file.
* Restore with:
```
./setup_openshift -r -e @vars.yml -e openshift_password=your_password
```
* Check restored Tower resources and inventory file.
