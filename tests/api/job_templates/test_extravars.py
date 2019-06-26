import json

from towerkit.exceptions import BadRequest
import fauxfactory
import pytest

from tests.api import APITest


@pytest.fixture(scope="function")
def variables_yaml(request):
    return 'ansible_host: localhost\nansible_user: ubuntu\n'


@pytest.fixture(scope="function")
def variables_json(request, variables_yaml):
    return '{"ansible_host": "localhost", "ansible_user": "ubuntu"}'


@pytest.fixture(scope="function")
def inventory_yaml(request, authtoken, api_inventories_pg, organization, variables_yaml):
    payload = dict(name="inventory-%s" % fauxfactory.gen_utf8(),
                   description="Test inventory",
                   organization=organization.id,
                   variables=variables_yaml)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def inventory_json(request, authtoken, api_inventories_pg, organization, variables_json):
    payload = dict(name="inventory-%s" % fauxfactory.gen_utf8(),
                   description="Test inventory",
                   organization=organization.id,
                   variables=variables_json)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# /groups
#
@pytest.fixture(scope="function")
def groups_json(request, authtoken, api_groups_pg, inventory_json, variables_json):
    payload = dict(name="group-%s" % fauxfactory.gen_utf8(),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def groups_yaml(request, authtoken, api_groups_pg, inventory_json, variables_yaml):
    payload = dict(name="group-%s" % fauxfactory.gen_utf8(),
                   inventory=inventory_json.id,
                   variables=variables_yaml)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# /hosts
#
@pytest.fixture(scope="function")
def hosts_json(request, authtoken, api_hosts_pg, inventory_json, variables_json):
    payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                   inventory=inventory_json.id,
                   variables=variables_json)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def hosts_yaml(request, authtoken, api_hosts_pg, inventory_json, variables_yaml):
    payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                   inventory=inventory_json.id,
                   variables=variables_yaml)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


#
# /job_templates
#
@pytest.fixture(scope="function")
def job_templates_json(request, authtoken, api_job_templates_pg, project, ssh_credential, inventory_json, variables_json):

    payload = dict(name="template-%s" % fauxfactory.gen_utf8(),
                   extra_vars=variables_json,
                   inventory=inventory_json.id,
                   job_type='run',
                   project=project.id,
                   playbook='debug.yml',
                   credential=ssh_credential.id)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_templates_yaml(request, authtoken, api_job_templates_pg, project, ssh_credential, inventory_yaml, variables_yaml):
    payload = dict(name="template-%s" % fauxfactory.gen_utf8(),
                   extra_vars=variables_yaml,
                   inventory=inventory_yaml.id,
                   job_type='run',
                   project=project.id,
                   playbook='debug.yml',
                   credential=ssh_credential.id)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.mark.usefixtures('authtoken')
class TestExtraVarsStoreRetreiveJsonYaml(APITest):
    """For API objects that support a 'variables' (or 'extra_vars') attribute,
    verify they support storing and retrieving JSON/YAML data.

    From AC 1035
    """

    #
    # /inventories
    #
    def test_inventory_variables_attr_yaml_post(self, inventory_yaml):
        """Assert that storing (POST) valid YAML in inventory.variables succeeds"""
        try:
            inventory_yaml.variables
        except Exception:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.json.variables)

    def test_inventory_variables_attr_yaml_patch(self, inventory_yaml, variables_yaml):
        """Assert that storing (PATCH) valid YAML in inventory.variables succeeds"""
        inventory_yaml.patch(variables=variables_yaml)
        inventory_yaml.get()
        try:
            inventory_yaml.variables
        except Exception:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.json.variables)

    def test_inventory_variables_attr_yaml_put(self, inventory_yaml, variables_yaml):
        """Assert that storing (PUT) valid YAML in inventory.variables succeeds"""
        inventory_yaml.variables = variables_yaml
        inventory_yaml.put()
        inventory_yaml.get()
        try:
            inventory_yaml.variables
        except Exception:
            pytest.fail("inventory variables not stored as YAML data: %s" % inventory_yaml.json.variables)

    def test_inventory_variables_attr_json_post(self, inventory_json):
        """Assert that storing (POST) valid JSON in inventory.variables succeeds"""
        try:
            inventory_json.variables
        except Exception:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.json.variables)

    def test_inventory_variables_attr_json_patch(self, inventory_json, variables_json):
        """Assert that storing (PATCH) valid JSON in inventory.variables succeeds"""
        inventory_json.patch(variables=variables_json)
        inventory_json.get()
        try:
            inventory_json.variables
        except Exception:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.json.variables)

    def test_inventory_variables_attr_json_put(self, inventory_json, variables_json):
        """Assert that storing (PUT) valid JSON in inventory.variables succeeds"""
        inventory_json.variables = variables_json
        inventory_json.put()
        inventory_json.get()
        try:
            inventory_json.variables
        except Exception:
            pytest.fail("inventory variables not stored as JSON data: %s" % inventory_json.json.variables)

    def test_inventory_variables_attr_invalid(self, inventory_yaml):
        """Assert that storing invalid YAML/JSON in inventory.variables fails"""
        with pytest.raises(BadRequest):
            inventory_yaml.patch(variables="{")

    #
    # /groups
    #
    def test_groups_variables_attr_yaml_post(self, groups_yaml):
        """Assert that storing (POST) valid YAML in groups.variables succeeds"""
        try:
            groups_yaml.variables
        except Exception:
            pytest.fail("groups variables not stored as YAML data: %s" % groups_yaml.json.variables)

    def test_groups_variables_attr_json_post(self, groups_json):
        """Assert that storing (POST) valid JSON in groups.variables succeeds"""
        try:
            groups_json.variables
        except Exception:
            pytest.fail("groups variables not stored as JSON data: %s" % groups_json.json.variables)

    def test_groups_variables_attr_invalid(self, groups_yaml):
        """Assert that storing invalid YAML/JSON in groups.variables fails"""
        with pytest.raises(BadRequest):
            groups_yaml.patch(variables="{")

    #
    # /hosts
    #
    def test_hosts_variables_attr_yaml_post(self, hosts_yaml):
        try:
            hosts_yaml.variables
        except Exception:
            pytest.fail("hosts variables not stored as YAML data: %s" % hosts_yaml.json.variables)

    def test_hosts_variables_attr_json_post(self, hosts_json):
        try:
            hosts_json.variables
        except Exception:
            pytest.fail("hosts variables not stored as JSON data: %s" % hosts_json.json.variables)

    def test_hosts_variables_attr_invalid(self, hosts_yaml):
        """Assert that storing invalid YAML/JSON in hosts.variables fails"""
        with pytest.raises(BadRequest):
            hosts_yaml.patch(variables="{")

    #
    # /job_templates
    #
    @pytest.mark.yolo
    def test_job_templates_extra_var_attr_yaml_post(self, job_templates_yaml):
        """Assert that valid yaml is properly stored/retrieved in extra_vars"""
        try:
            job_templates_yaml.extra_vars
        except Exception:
            pytest.fail("job_templates extra_vars not stored as YAML data: %s" % job_templates_yaml.json.extra_vars)

    @pytest.mark.yolo
    def test_job_templates_extra_var_attr_json_post(self, job_templates_json):
        """Assert that valid json is properly stored/retrieved in extra_vars"""
        try:
            json.loads(job_templates_json.extra_vars)
        except Exception:
            pytest.fail("job_templates extra_vars not stored as JSON data: %s" % job_templates_json.extra_vars)
