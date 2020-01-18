import logging
import json
import uuid

from awxkit.utils import not_provided
import fauxfactory
import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def api_inventory_sources_options_json(api_inventory_sources_pg):
    return api_inventory_sources_pg.options().json


# Various choices values from the OPTIONS request
@pytest.fixture(scope="function")
def azure_region_choices(api_inventory_sources_options_json):
    """Return field 'azure_ret_choices' from the inventory_sources OPTIONS json."""
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['azure_region_choices'])


@pytest.fixture(scope="function")
def gce_region_choices(api_inventory_sources_options_json):
    """Return field 'gce_ret_choices' from the inventory_sources OPTIONS json."""
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['gce_region_choices'])


@pytest.fixture(scope="function")
def ec2_region_choices(api_inventory_sources_options_json):
    """Return field 'ec2_ret_choices' from the inventory_sources OPTIONS json."""
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['ec2_region_choices'])


@pytest.fixture(scope="function")
def ec2_group_by_choices(api_inventory_sources_options_json):
    """Return field 'ec2_group_by_choices' from the inventory_sources OPTIONS json."""
    return dict(api_inventory_sources_options_json['actions']['GET']['group_by']['ec2_group_by_choices'])


@pytest.fixture(scope="function")
def host_config_key():
    """Returns a uuid4 string for use as a host_config_key."""
    return str(uuid.uuid4())


@pytest.fixture(scope="function")
def ansible_default_ipv4(ansible_facts):
    """Return the ansible_default_ipv4 from ansible_facts of the system under test."""
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for {0} systems found, but returning "
                    "only the first".format(len(ansible_facts)))
    return list(ansible_facts.values())[0]['ansible_facts']['ansible_default_ipv4']['address']


@pytest.fixture(scope="function")
def inventory(factories, organization):
    return factories.inventory(organization=organization, localhost=None)


@pytest.fixture(scope="function")
def another_inventory(factories, organization):
    return factories.inventory(organization=organization, localhost=None)


@pytest.fixture(scope="function")
def custom_inventory_update_with_status_completed(custom_inventory_source):
    """Launches an inventory sync."""
    update = custom_inventory_source.update().wait_until_completed()
    assert update.is_successful, 'Custom inventory update fixture not successful, stdout:\n{}'.format(
        update.result_stdout)
    return update


@pytest.fixture(scope="function")
def host_with_default_ipv4_in_variables(factories, inventory, ansible_default_ipv4):
    """Create a random inventory host where ansible_host == ansible_default_ipv4."""
    host = factories.host(inventory=inventory,
                          variables=json.dumps(dict(ansible_host=ansible_default_ipv4,
                                                    ansible_connection="local")))
    return host


@pytest.fixture(scope="function")
def group(factories, inventory):
    return factories.group(inventory=inventory)


@pytest.fixture(scope="function")
def inventory_source(factories, inventory_script):
    organization = inventory_script.related.organization.get()
    inventory = factories.inventory(
        organization=organization,
        variables=json.dumps(dict(ansible_connection="local"))
    )
    return factories.inventory_source(inventory=inventory, source_script=inventory_script)


@pytest.fixture(scope="function")
def host_local(factories, inventory, group):
    host = factories.host(name="local", description="a non-random local host", inventory=inventory)
    group.add_host(host)
    return host


@pytest.fixture(scope="function")
def host_with_default_connection(factories, inventory, group):
    host = factories.host(name="localhost", description="a non-random local host", inventory=inventory,
                          variables=not_provided)
    group.add_host(host)
    return host


@pytest.fixture(scope="function")
def host_without_group(factories, inventory):
    host = factories.host(description="a host detached from any groups - %s" % fauxfactory.gen_utf8(),
                          inventory=inventory)
    return host


@pytest.fixture(scope="function")
def host(factories, inventory, group):
    host = factories.host(inventory=inventory)
    group.add_host(host)
    return host


@pytest.fixture(scope="function")
def script_source(request):
    fixture_args = request.node.get_closest_marker('fixture_args')
    if fixture_args and 'source_script' in fixture_args.kwargs:
        return fixture_args.kwargs['source_script']

    group_name = f'group_{fauxfactory.gen_utf8()}'
    script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
inventory = dict()
inventory['{0}'] = dict()
inventory['{0}']['hosts'] = list()
""".format(group_name)
    for i in range(5):
        host_name = f"host_{fauxfactory.gen_utf8()}"
        script += f"inventory['{group_name}']['hosts'].append('{host_name}')\n"
    script += f"inventory['{group_name}']['vars'] = dict(ansible_host='127.0.0.1', ansible_connection='local')\n"
    script += "print(json.dumps(inventory))\n"
    log.debug(script)
    return script


@pytest.fixture(scope="function")
def inventory_script(factories, script_source, organization):
    return factories.inventory_script(organization=organization, script=script_source)


@pytest.fixture(scope="function")
def aws_inventory_source(factories, aws_credential):
    return factories.inventory_source(credential=aws_credential, source='ec2')


@pytest.fixture(scope="function")
def azure_inventory_source(factories, azure_credential):
    return factories.inventory_source(credential=azure_credential, source='azure_rm')


@pytest.fixture(scope="function")
def gce_inventory_source(factories, gce_credential):
    return factories.inventory_source(credential=gce_credential, source='gce')


@pytest.fixture(scope="function")
def vmware_inventory_source(vmware_credential):
    pytest.skip('Currently without access to functional VMware system')


@pytest.fixture(scope="function")
def openstack_inventory_source(factories, openstack_v3_credential):
    return factories.inventory_source(source='openstack', credential=openstack_v3_credential)


@pytest.fixture(scope="function")
def custom_inventory_source(request, authtoken, inventory_source):
    return inventory_source.get()


@pytest.fixture(scope="function", params=['aws', 'azure', 'gce', 'vmware', 'openstack'])
def cloud_inventory_source(request):
    return request.getfixturevalue(request.param + '_inventory_source')


@pytest.fixture(scope="class")
def _parallel_run_all_inventory_updates(request, class_factories):
    source_and_cred = {
        'ec2': 'aws_credential',
        'azure_rm': 'azure_credential',
        'gce': 'gce_credential',
        'openstack': 'openstack_v3_credential'
    }
    inv_sources = {}
    for source, cred_fixture in source_and_cred.items():
        cred = request.getfixturevalue(cred_fixture)
        inv_sources[source] = class_factories.inventory_source(source=source, credential=cred)
        if source == 'azure_rm':
            inv_sources[source].source_vars = json.dumps({
                'group_by_location': True,
                'group_by_os_family': True,
                'group_by_resource_group': True,
                'group_by_security_group': True,
                'group_by_tag': True
                })

    updates = []
    # Start all requests
    for inv_source in inv_sources.values():
        updates.append(inv_source.update())

    # Wait for requests to finish
    for update in updates:
        update.wait_until_completed()

    inventories = {key: inv_source.related.inventory.get() for key, inv_source in inv_sources.items()}
    return inventories


@pytest.fixture(scope="class", params=['ec2', 'azure_rm', 'gce', 'openstack'], ids=['aws', 'azure', 'gce', 'openstack'])
def cloud_inventory(request, class_factories, _parallel_run_all_inventory_updates):
    return _parallel_run_all_inventory_updates[request.param]


@pytest.fixture(scope="class", params=['ec2', 'azure_rm', 'gce', 'openstack'], ids=['aws', 'azure', 'gce', 'openstack'])
def inventory_with_known_schema(request, class_factories, _parallel_run_all_inventory_updates):
    return _parallel_run_all_inventory_updates[request.param]


# Convenience fixture that iterates through cloud_groups that support source_regions
@pytest.fixture(scope="function", params=['aws', 'azure', 'gce'])
def cloud_inventory_source_supporting_source_regions(request):
    return request.getfixturevalue(request.param + '_inventory_source')


@pytest.fixture
def inventory_script_code_with_sleep():
    def fn(sleep_time):
        return "#!/usr/bin/env python\nimport time\ntime.sleep({})\nprint('{{}}')\n".format(sleep_time)
    return fn
