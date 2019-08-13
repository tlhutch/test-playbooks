# Minimum OpenStack config for QE Tests
Some measure of openstack testing has been around for a long time, testing against a devstack in ec2.

While in the future this may change, we are tied to what was once done until these versions fall out of support.

This is what that devstack needs for our older tests to run against it.

* User specified by `openstack_v3` creds in `tower-qa/config/credentials.yml`
* An instance running in the project ^ user is associated with

HOW?

1) Get super admin auth from @chrismeyersfsu or @kdelee or someone else on qe or api team that has it
2) login and get openstack rc file to help you with CLI access
3) download python-openstack-client package to a venv
4) do following:

```
# download rc file to get right env vars to authenticate as super admin
source ~/Downloads/admin-openrc.sh
# enter password

# take note of domain and project id
openstack domain create --description "test_domain" test_domain
openstack project create --description project01 project01 --domain test_domain
openstack user create --domain test_domain --project project01 domain_user --password-prompt
openstack role add --project project01 --user admin domain_user

# Now copy rc file and edit it to contain domain and project id for test_domain and project01
# also update auth URL to OS_AUTH_URL=http://ec2-54-237-102-215.compute-1.amazonaws.com:5000/v3
# reminder: project is other word for tenant
# export OS_TENANT_ID=70c96635080c4048bec573dd5c989b69
# export OS_TENANT_NAME="project01"
# export OS_DOMAIN_NAME="test_domain"
# export OS_DOMAIN_ID=34199b19c728407e9b9b5d6b60902b5b

cp ~/Downloads/admin-openrc.sh ~/Downloads/domain_user-openrc.sh
# may need to look up new image id by using "openstack image list"
openstack server create --image 9697af3f-aa59-4a4f-8341-088e4f90a0fd --flavor m1.tiny foo
```

Sample admin RC file:
```

#!/bin/bash

# To use an Openstack cloud you need to authenticate against keystone, which
# returns a **Token** and **Service Catalog**.  The catalog contains the
# endpoint for all services the user/tenant has access to - including nova,
# glance, keystone, swift.
#
# *NOTE*: Using the 2.0 *auth api* does not mean that compute api is 2.0.  We
# will use the 1.1 *compute api*
export OS_AUTH_URL=http://ec2-54-237-102-215.compute-1.amazonaws.com:5000/v2.0

# With the addition of Keystone we have standardized on the term **tenant**
# as the entity that owns the resources.
export OS_TENANT_ID=042f04f75567472bbc7ff33f245bae4b
export OS_TENANT_NAME="admin"

# In addition to the owning entity (tenant), openstack stores the entity
# performing the action as the **user**.
export OS_USERNAME="admin"

# With Keystone you pass the keystone password.
echo "Please enter your OpenStack Password: "
read -sr OS_PASSWORD_INPUT
export OS_PASSWORD=$OS_PASSWORD_INPUT

# If your configuration has multiple regions, we set that information here.
# OS_REGION_NAME is optional and only valid in certain environments.
export OS_REGION_NAME="RegionOne"
# Don't leave a blank variable, unset it if it was empty
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
```

Sample domain user RC file:
```

#!/bin/bash

# To use an Openstack cloud you need to authenticate against keystone, which
# returns a **Token** and **Service Catalog**.  The catalog contains the
# endpoint for all services the user/tenant has access to - including nova,
# glance, keystone, swift.
#
# *NOTE*: Using the 2.0 *auth api* does not mean that compute api is 2.0.  We
# will use the 1.1 *compute api*
export OS_AUTH_URL=http://ec2-54-237-102-215.compute-1.amazonaws.com:5000/v3

# With the addition of Keystone we have standardized on the term **tenant**
# as the entity that owns the resources.
export OS_TENANT_ID=70c96635080c4048bec573dd5c989b69
export OS_TENANT_NAME="project01"
unset OS_DOMAIN_NAME
unset OS_DOMAIN_ID
export OS_DOMAIN_NAME="test_domain"
export OS_DOMAIN_ID=34199b19c728407e9b9b5d6b60902b5b

# In addition to the owning entity (tenant), openstack stores the entity
# performing the action as the **user**.
export OS_USERNAME="domain_user"

# With Keystone you pass the keystone password.
echo "Please enter your OpenStack Password: "
read -sr OS_PASSWORD_INPUT
export OS_PASSWORD=$OS_PASSWORD_INPUT

# If your configuration has multiple regions, we set that information here.
# OS_REGION_NAME is optional and only valid in certain environments.
export OS_REGION_NAME="RegionOne"
# Don't leave a blank variable, unset it if it was empty
if [ -z "$OS_REGION_NAME" ]; then unset OS_REGION_NAME; fi
```

**NOTE: If you must do this, then the tenant and domain id's have probably changed!
Possibly other things like the ec2 url as well may be different.**
