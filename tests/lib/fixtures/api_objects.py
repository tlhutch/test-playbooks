import pytest
import json
import yaml
import common.utils
from tests.api import Base_Api_Test

@pytest.fixture(scope="class")
def random_organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_unicode(),
                   description="Random organization",)
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def random_project(request, authtoken, api_projects_pg, random_organization):
    # Create project
    payload = dict(name="project-%s" % common.utils.random_unicode(),
                   organization=random_organization.id,
                   scm_type='hg',
                   scm_url='https://bitbucket.org/jlaska/ansible-helloworld',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)

    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Wait for project update to complete
    updates_pg = obj.get_related('project_updates')
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop()
    count = 0
    while count <30 and latest_update_pg.status.lower() != 'successful':
        latest_update_pg.get()
        count +=1

    return obj

@pytest.fixture(scope="class")
def admin_user(request, authtoken, api_users_pg):
    return api_users_pg.get(username__iexact='admin').results[0]

@pytest.fixture(scope="class")
def random_inventory(request, authtoken, api_inventories_pg, random_organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=random_organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /groups
#
@pytest.fixture(scope="class")
def random_group(request, authtoken, api_groups_pg, random_inventory):
    payload = dict(name="group-%s" % common.utils.random_unicode(),
                   inventory=random_inventory.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /inventory_source
#
@pytest.fixture(scope="class")
def random_inventory_source(request, authtoken, random_group):
    return random_group.get_related('inventory_source')

#
# /credentials
#

@pytest.fixture(scope="class")
def random_ssh_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    # Create ssh credential
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password=testsetup.credentials['ssh']['password'],
                  )
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def random_ssh_credential_ask(request, authtoken, api_credentials_pg, admin_user, testsetup):
    # Create ssh credential with 'ASK' password
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="machine credential with ASK password - %s" % common.utils.random_unicode(),
                   kind='ssh',
                   user=admin_user.id,
                   username=testsetup.credentials['ssh']['username'],
                   password='ASK',
                  )
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def random_aws_credential(request, authtoken, api_credentials_pg, admin_user, testsetup):
    # Create scm credential with scm_key_unlock='ASK'
    payload = dict(name="credentials-%s" % common.utils.random_unicode(),
                   description="AWS credential %s" % common.utils.random_unicode(),
                   kind='aws',
                   user=admin_user.id,
                   username=testsetup.credentials['cloud']['aws']['username'],
                   password=testsetup.credentials['cloud']['aws']['password'],
                  )
    obj = api_credentials_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def random_aws_group(request, authtoken, api_groups_pg, random_inventory, random_aws_credential):
    payload = dict(name="aws-group-%s" % common.utils.random_ascii(),
                   description="AWS group %s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,
                   credential=random_aws_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'ec2'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='ec2', credential=random_aws_credential.id)
    return obj

#
# /inventory_source
#
@pytest.fixture(scope="class")
def random_aws_inventory_source(request, authtoken, random_aws_group):
    return random_aws_group.get_related('inventory_source')

#
# /hosts
#
@pytest.fixture(scope="class")
def random_host(request, authtoken, api_hosts_pg, random_inventory, random_group):
    payload = dict(name="host-%s" % common.utils.random_unicode(),
                   group=random_group.id,
                   inventory=random_inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /job_templates
#
@pytest.fixture(scope="function")
def random_job_template_no_credential(request, authtoken, api_job_templates_pg, random_project, random_inventory):
    '''Define a job_template with no machine credential'''

    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template without credentials - %s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,
                   job_type='run',
                   project=random_project.id,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def random_job_template(request, authtoken, api_job_templates_pg, random_project, random_inventory, random_ssh_credential):
    '''Define a job_template with a valid machine credential'''

    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with machine credentials - %s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,
                   job_type='run',
                   project=random_project.id,
                   credential=random_ssh_credential.id,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj
