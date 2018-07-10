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
* Delete your resources.
* Restore with:
```
./setup_openshift -r -e @vars.yml -e openshift_password=your_password
```
* Check restored Tower resources.
* Cluster topology should be restored. So for instance, if you had three Tower pods to begin with, you should end up with three Tower pods.

To verify backup restore with an external database:
* You are going to have to find a postgres instance to use. You can borrow one from the nightlies.
* You are going to have to install Tower with the following variables:
```
pg_hostname=ec2-fake.amazonaws.com  
#
# Will use an emptyDir volume for the postgres pod.
# Use for demos or testing purposes only
# openshift_pg_emptydir=false
# pg_pvc_name=postgresql
pg_username=awx
pg_password=Th1sP4ssd
pg_database=awx
pg_port=5432
```
* You are going to have to [enable](https://bosnadev.com/2015/12/15/allow-remote-connections-postgresql-database-server/) postgres to listen to remote connections.
* Create some Tower resource and perform a backup.
* Authenticate to your postgres server as the admin "postgres" user.
* Grant the "awx" user adequate permissions:
```
ALTER USER awx CREATEDB;
```
* Delete these resources, perform a restoration.
* Tower resources should be restored as well as the number of Tower pods (if we started out with three, we should have three again).

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) July 9, 2018.
