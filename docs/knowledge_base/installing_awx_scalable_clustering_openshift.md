### Installing AWX on OpenShift in VRTX

To install AWX on OpenShift, clone the `tower-packaging` repository.

You will need to create a persistent volume claim. Create a yaml file as follows:
```
Simfarm@ovpn-125-95:~/Git/tower-packaging/setup_cluster$ cat pvc.yml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
 name: postgresql
 namespace: tower-qe
spec:
 accessModes:
  - ReadWriteOnce
 storageClassName: glusterfs-storage
 resources:
   requests:
     storage: 10Gi
```

Use the `oc` command to create the pvc using this yaml file:
```
Simfarm@ovpn-125-95:~/Git/tower-packaging/setup_cluster$ oc create -f pvc.yml -n tower-qe
```

Add the following to the cluster inventory file:
```
--- a/setup_cluster/inventory
+++ b/setup_cluster/inventory
@@ -76,3 +76,8 @@ pg_port=5432
 # Container networking configuration
 # Set the tower_task and tower_web containers' search domain(s)
 #tower_container_search_domains=example.com,ansible.com
+
+openshift_host=https://console.openshift.ansible.eng.rdu2.redhat.com:8443
+tower_openshift_project=tower-qe
+openshift_user=chrwang # update with your RHT username
+tower_web_openshift_image=awx_web:latest
```

Run the setup playbook:
```
Simfarm@ovpn-125-95:~/Git/tower-packaging/setup_cluster$ ansible-playbook -i inventory install.yml -e openshift_password=very_secret -v
```
