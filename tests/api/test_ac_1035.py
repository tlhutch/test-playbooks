import pytest
import json
import yaml
import common.tower.license
import common.utils
from tests.api import Base_Api_Test

@pytest.fixture(scope="class")
def organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_ascii(),
                   description="Test organization",)
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

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
def inventory_yaml(request, authtoken, api_inventories_pg, organization, variables_yaml):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Test inventory",
                   organization=organization.id,
                   variables=variables_yaml)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def inventory_json(request, authtoken, api_inventories_pg, organization, variables_json):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Test inventory",
                   organization=organization.id,
                   variables=variables_json)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

#
# /groups
#
@pytest.fixture(scope="class")
def groups_json(request, authtoken, api_groups_pg, inventory_json, variables_json):
    payload = dict(name="group-%s" % common.utils.random_ascii(),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def groups_yaml(request, authtoken, api_groups_pg, inventory_json, variables_yaml):
    payload = dict(name="group-%s" % common.utils.random_ascii(),
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
    payload = dict(name="host-%s" % common.utils.random_ascii(),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def hosts_yaml(request, authtoken, api_hosts_pg, inventory_json, variables_yaml):
    payload = dict(name="host-%s" % common.utils.random_ascii(),
                   inventory=inventory_json.id,
                   variables=variables_yaml)
    obj = api_hosts_pg.post(payload)
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
            json.loads(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_yaml.variables)

    def test_inventory_variable_yaml_patch(self, inventory_yaml, variables_yaml):
        inventory_yaml.patch(variables=variables_yaml)
        inventory_yaml.get()
        try:
            json.loads(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_yaml.variables)

    def test_inventory_variable_yaml_put(self, inventory_yaml, variables_yaml):
        inventory_yaml.variables = variables_yaml
        inventory_yaml.put()
        inventory_yaml.get()
        try:
            json.loads(inventory_yaml.variables)
        except Exception, e:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_yaml.variables)

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
            json.loads(groups_yaml.variables)
        except Exception, e:
            pytest.fail("groups variables not stored as JSON data: %s" % groups_yaml.variables)

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
            json.loads(hosts_yaml.variables)
        except Exception, e:
            pytest.fail("hosts variables not stored as JSON data: %s" % hosts_yaml.variables)

    def test_hosts_variable_json_post(self, hosts_json):
        try:
            json.loads(hosts_json.variables)
        except Exception, e:
            pytest.fail("hosts variables not stored as JSON data: %s" % hosts_json.variables)
