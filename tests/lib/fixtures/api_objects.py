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
def random_inventory(request, authtoken, api_inventories_pg, random_organization):
    payload = dict(name="inventory-%s" % common.utils.random_unicode(),
                   description="Random inventory",
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
# /hosts
#
@pytest.fixture(scope="class")
def random_host(request, authtoken, api_hosts_pg, random_inventory):
    payload = dict(name="host-%s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /job_templates
#
@pytest.fixture(scope="class")
def random_job_template(request, authtoken, api_job_templates_pg, random_project, random_inventory):

    payload = dict(name="template-%s" % common.utils.random_unicode(),
                   description="Random job_template",
                   inventory=random_inventory.id,
                   job_type='run',
                   project=random_project.id,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj
