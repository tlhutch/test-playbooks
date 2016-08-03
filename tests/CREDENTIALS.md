# CREDENTIALS.md

This page describes the `credentials.yml` file.

## Azure Classic

You 
```
openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout azure.pem -out azure.pem
openssl x509 -inform pem -in azure.pem -outform der -out azure.cer
```

Upload your azure.cer file at https://manage.windowsazure.com/AnsibleWorks.onmicrosoft.com#Workspaces/AdminTasks/ListManagementCertificates

Update credentials.yml file with the azure.pem file data. username is the subscription id listed at the url you uploaded the certificate at.
```
  azure_classic:
    ssh_key_data: |
      -----BEGIN RSA PRIVATE KEY-----
      ...
      -----END RSA PRIVATE KEY-----
      -----BEGIN CERTIFICATE-----
      ...
      -----END CERTIFICATE-----
    username: <subscription_id>
```
