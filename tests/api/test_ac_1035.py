import pytest
import json
import yaml
import common.tower.license
import common.utils
from tests.api import Base_Api_Test

@pytest.fixture(scope="class")
def variables_yaml(request):
    return yaml.load('''
variables: |
    ansible_ssh_host: localhost
    ansible_ssh_user: ubuntu
''')['variables']

@pytest.fixture(scope="class")
def variables_json(request, variables_yaml):
    return json.dumps(variables_yaml)

@pytest.fixture(scope="class")
def inventory_yaml(request, authtoken, api_inventories_pg, random_organization, variables_yaml):
    payload = dict(name="inventory-%s" % common.utils.random_unicode(),
                   description="Test inventory",
                   organization=random_organization.id,
                   variables=variables_yaml)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def inventory_json(request, authtoken, api_inventories_pg, random_organization, variables_json):
    payload = dict(name="inventory-%s" % common.utils.random_unicode(),
                   description="Test inventory",
                   organization=random_organization.id,
                   variables=variables_json)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /groups
#
@pytest.fixture(scope="class")
def groups_json(request, authtoken, api_groups_pg, inventory_json, variables_json):
    payload = dict(name="group-%s" % common.utils.random_unicode(),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def groups_yaml(request, authtoken, api_groups_pg, inventory_json, variables_yaml):
    payload = dict(name="group-%s" % common.utils.random_unicode(),
                   inventory=inventory_json.id,
                   variables=variables_yaml)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /hosts
#
@pytest.fixture(scope="class")
def hosts_json(request, authtoken, api_hosts_pg, inventory_json, variables_json):
    payload = dict(name="host-%s" % common.utils.random_unicode(),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def hosts_yaml(request, authtoken, api_hosts_pg, inventory_json, variables_yaml):
    payload = dict(name="host-%s" % common.utils.random_unicode(),
                   inventory=inventory_json.id,
                   variables=variables_yaml)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /job_templates
#
@pytest.fixture(scope="class")
def job_templates_json(request, authtoken, api_job_templates_pg, random_project, inventory_json, variables_json):

    payload = dict(name="template-%s" % common.utils.random_unicode(),
                   extra_vars=variables_json,
                   inventory=inventory_json.id,
                   job_type='run',
                   project=random_project.id,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def job_templates_yaml(request, authtoken, api_job_templates_pg, random_project, inventory_yaml, variables_yaml):
    payload = dict(name="template-%s" % common.utils.random_unicode(),
                   extra_vars=variables_yaml,
                   inventory=inventory_yaml.id,
                   job_type='run',
                   project=random_project.id,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
@pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000')
class Test_AC_1035(Base_Api_Test):
    '''
    Test JSON variable POST, PUT, PATCH
    Test YAML variable POST, PUT, PATCH
    Test related -> variable_data
    '''
    #
    # /inventories
    #
    def test_inventory_variable_yaml_post(self, inventory_yaml):
        try:
            yaml.load(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.variables)

    def test_inventory_variable_yaml_patch(self, inventory_yaml, variables_yaml):
        inventory_yaml.patch(variables=variables_yaml)
        inventory_yaml.get()
        try:
            yaml.load(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.variables)

    def test_inventory_variable_yaml_put(self, inventory_yaml, variables_yaml):
        inventory_yaml.variables = variables_yaml
        inventory_yaml.put()
        inventory_yaml.get()
        try:
            yaml.load(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.variables)

    def test_inventory_variable_json_post(self, inventory_json):
        try:
            json.loads(inventory_json.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.variables)

    def test_inventory_variable_json_patch(self, inventory_json, variables_json):
        inventory_json.patch(variables=variables_json)
        inventory_json.get()
        try:
            json.loads(inventory_json.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.variables)

    def test_inventory_variable_json_put(self, inventory_json, variables_json):
        inventory_json.variables = variables_json
        inventory_json.put()
        inventory_json.get()
        try:
            json.loads(inventory_json.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.variables)

    #
    # /groups
    #
    def test_groups_variable_yaml_post(self, groups_yaml):
        try:
            yaml.load(groups_yaml.variables)
        except Exception, e:
            pytest.fail("groups variables not stored as YAML data: %s" % groups_yaml.variables)

    def test_groups_variable_json_post(self, groups_json):
        try:
            json.loads(groups_json.variables)
        except Exception, e:
            pytest.fail("groups variables not stored as JSON data: %s" % groups_json.variables)

    #
    # /hosts
    #
    def test_hosts_variable_yaml_post(self, hosts_yaml):
        try:
            yaml.load(hosts_yaml.variables)
        except Exception, e:
            pytest.fail("hosts variables not stored as YAML data: %s" % hosts_yaml.variables)

    def test_hosts_variable_json_post(self, hosts_json):
        try:
            json.loads(hosts_json.variables)
        except Exception, e:
            pytest.fail("hosts variables not stored as JSON data: %s" % hosts_json.variables)

    #
    # /job_templates
    #
    def test_job_templates_extra_var_yaml_post(self, job_templates_yaml):
        try:
            yaml.load(job_templates_yaml.extra_vars)
        except Exception, e:
            pytest.fail("job_templates variables not stored as YAML data: %s" % job_templates_yaml.extra_vars)

    def test_job_templates_extra_var_json_post(self, job_templates_json):
        try:
            json.loads(job_templates_json.extra_vars)
        except Exception, e:
            pytest.fail("job_templates variables not stored as JSON data: %s" % job_templates_json.extra_vars)
