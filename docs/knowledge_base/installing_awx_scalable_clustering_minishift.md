### Install AWX branch `scalable_clustering` on Minishift

Instantiate Minishift VM with adequate resources:
```
minishift start --cpus 4 --memory 8192
```

Update the inventory file under `installer/inventory` as follows:
```
--- a/installer/inventory
+++ b/installer/inventory
@@ -6,13 +6,13 @@ localhost ansible_connection=local ansible_python_interpreter="/usr/bin/env pyth
 # Otherwise the setup playbook will install the official Ansible images. Versions may
 # be selected based on: latest, 1, 1.0, 1.0.0, 1.0.0.123
 # by default the base will be used to search for ansible/awx_web and ansible/awx_task
-dockerhub_base=ansible
-dockerhub_version=latest
+# dockerhub_base=ansible
+# dockerhub_version=latest

 # This will create or update a default admin (superuser) account in AWX, if not provided
 # then these default values are used
-# default_admin_user=admin
-# default_admin_password=password
+default_admin_user=admin
+default_admin_password=fo0m4nchU

 # AWX Secret key
 # It's *very* important that this stay the same between upgrades or you will lose the ability to decrypt
@@ -21,10 +21,10 @@ awx_secret_key=awxsecret

 # Openshift Install
 # Will need to set -e openshift_password=developer -e docker_registry_password=$(oc whoami -t)
-# openshift_host=127.0.0.1:8443
-# awx_openshift_project=awx
-# openshift_user=developer
-# awx_node_port=30083
+openshift_host=192.168.64.7:8443  # exact IP changes; find yours with "minishift ip"
+awx_openshift_project=awx
+openshift_user=developer
+awx_node_port=30083

 # Standalone Docker Install
 postgres_data_dir=/tmp/pgdocker
@@ -35,9 +35,9 @@ host_port=80
 # Required for Standalone Docker Install if building the image on your own
 # Optional for Standalone Docker Install if using Dockerhub or another prebuilt registry
 # Define if you want the image pushed to a registry. The container definition will also use these images
-# docker_registry=172.30.1.1:5000
-# docker_registry_repository=awx
-# docker_registry_username=developer
+docker_registry=172.30.1.1:5000
+docker_registry_repository=awx
+docker_registry_username=developer


 # Docker_image will not attempt to push to remote if the image already exists locally
@@ -61,7 +61,7 @@ pg_port=5432
 #                  Thus this setting must be set to False which will trigger a local build. To view the
 #                  typical dependencies that you might need to install see:
 #                  installer/image_build/files/Dockerfile.sdist
-# use_container_for_build=true
+use_container_for_build=false
```

Set environment variables:
```
  eval $(minishift docker-env)
  eval $(minishift oc-env)
```

Invoke setup playbook:
```
(tower-qa) Simfarm@chrwang-OSX:~/Git/awx/installer$ ansible-playbook -i inventory install.yml -e openshift_password=developer  -e docker_registry_password=$(oc whoami -t)
```

Playbook will fail as follows:
```
TASK [openshift : Tag and push web image to registry] ******************************************************************************
fatal: [localhost -> localhost]: FAILED! => {"changed": false, "msg": "Error pushing image 172.30.1.1:5000/awx/awx_web:1.0.1.637 - unauthorized: authentication required. Try logging into 172.30.1.1:5000 first."}
```

Playbook logic needs some work. So perform a few actions manually:
```
(tower-qa) Simfarm@chrwang-OSX:~/Git/awx/installer$ oc login -u developer -p developer
Login successful.
```
```
(tower-qa) Simfarm@chrwang-OSX:~/Git/awx/installer$ docker login -u developer -p $(oc whoami -t) 172.30.1.1:5000
WARNING! Using --password via the CLI is insecure. Use --password-stdin.
Login Succeeded
```

After that, rerun your setup playbook and you should be good to go.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) January 12, 2018.
