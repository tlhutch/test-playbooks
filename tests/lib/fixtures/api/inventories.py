import logging
import json
import uuid
import re

from towerkit.utils import not_provided
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
def host_with_default_ipv4_in_variables(factories, group, ansible_default_ipv4):
    """Create a random inventory host where ansible_host == ansible_default_ipv4."""
    host = factories.host(inventory=group.ds.inventory,
                          variables=json.dumps(dict(ansible_host=ansible_default_ipv4,
                                                    ansible_connection="local")))
    group.add_host(host)
    return host


@pytest.fixture(scope="function")
def group(factories, inventory):
    return factories.group(inventory=inventory)


@pytest.fixture(scope="function")
def inventory_source(group):
    return group.related.inventory_source.get()


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

    group_name = re.sub(r"[\']", "", "group-%s" % fauxfactory.gen_utf8())
    script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
inventory = dict()
inventory['{0}'] = list()
""".format(group_name)
    for i in range(5):
        host_name = re.sub(r"[\':]", "", "host-%s" % fauxfactory.gen_utf8())
        script += "inventory['{0}'].append('{1}')\n".format(group_name, host_name)
    script += "print(json.dumps(inventory))\n"
    log.debug(script)
    return script


@pytest.fixture(scope="function")
def inventory_script(factories, script_source, organization):
    return factories.inventory_script(organization=organization, script=script_source)


@pytest.fixture(scope="function")
def aws_group(factories, inventory, aws_credential):
    group = factories.group(name="aws-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="AWS group %s" % fauxfactory.gen_utf8(),
                            source='ec2', inventory=inventory, credential=aws_credential)
    return group


@pytest.fixture(scope="function")
def aws_inventory_source(aws_group):
    return aws_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def azure_group(factories, inventory, azure_credential):
    group = factories.group(name="azure-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Microsoft Azure %s" % fauxfactory.gen_utf8(),
                            source='azure_rm', inventory=inventory, credential=azure_credential)
    return group


@pytest.fixture(scope="function")
def azure_inventory_source(azure_group):
    return azure_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def azure_ad_group(factories, inventory, azure_ad_credential):
    group = factories.group(name="azure-ad-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Microsoft Azure %s" % fauxfactory.gen_utf8(),
                            source='azure_rm', inventory=inventory, credential=azure_ad_credential)
    return group


@pytest.fixture(scope="function")
def azure_ad_inventory_source(azure_ad_group):
    return azure_ad_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def gce_group(factories, inventory, gce_credential):
    group = factories.group(name="gce-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Google Compute Engine %s" % fauxfactory.gen_utf8(),
                            source='gce', inventory=inventory, credential=gce_credential)
    return group


@pytest.fixture(scope="function")
def gce_inventory_source(gce_group):
    return gce_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def vmware_group(factories, inventory, vmware_credential):
    pytest.skip('Currently without access to functional VMware system')
    group = factories.group(name="vmware-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="VMware vCenter %s" % fauxfactory.gen_utf8(),
                            source='vmware', inventory=inventory, credential=vmware_credential,
                            source_vars="---\nvalidate_certs: false")
    return group


@pytest.fixture(scope="function")
def vmware_inventory_source(vmware_group):
    return vmware_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def openstack_v2_group(factories, inventory, openstack_v2_credential):
    group = factories.group(name="openstack-v2-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Openstack %s" % fauxfactory.gen_utf8(),
                            source='openstack', inventory=inventory, credential=openstack_v2_credential)
    return group


@pytest.fixture(scope="function")
def openstack_v2_inventory_source(openstack_v2_group):
    return openstack_v2_group.related.inventory_source.get()


@pytest.fixture(scope="function")
def openstack_v3_group(factories, inventory, openstack_v3_credential):
    group = factories.group(name="openstack-v3-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Openstack %s" % fauxfactory.gen_utf8(),
                            source='openstack', inventory=inventory, credential=openstack_v3_credential)
    return group


@pytest.fixture(scope="function")
def openstack_v3_inventory_source(request, authtoken, openstack_v3_group):
    return openstack_v3_group.related.inventory_source.get()


@pytest.fixture(scope="function", params=['openstack_v2', 'openstack_v3'])
def openstack_group(request):
    return request.getfixturevalue(request.param + '_group')


@pytest.fixture(scope="function")
def custom_group(factories, inventory, inventory_script):
    group = factories.group(name="custom-group-%s" % fauxfactory.gen_alphanumeric(),
                            description="Custom Group %s" % fauxfactory.gen_utf8(),
                            inventory=inventory, inventory_script=inventory_script,
                            variables=json.dumps(dict(my_group_variable=True)))
    return group


@pytest.fixture(scope="function")
def custom_inventory_source(request, authtoken, custom_group):
    return custom_group.related.inventory_source.get()


@pytest.fixture(scope="function", params=['aws', 'azure', 'azure_ad', 'gce', 'vmware',
                                          'openstack_v2', 'openstack_v3'])
def cloud_group(request):
    return request.getfixturevalue(request.param + '_group')


@pytest.fixture(scope="function", params=[('ec2', 'aws_credential'),
                                          ('azure_rm', 'azure_credential'),
                                          ('azure_rm', 'azure_ad_credential'),
                                          ('gce', 'gce_credential'),
                                          ('vmware', 'vmware_credential'),
                                          ('openstack', 'openstack_v2_credential'),
                                          ('openstack', 'openstack_v3_credential')
    ], ids=['aws', 'azure', 'azure_ad', 'gce', 'vmware', 'openstack_v2', 'openstack_v3'])
def cloud_inventory(request, factories):
    inv_source, cred_fixture = request.param
    if inv_source == 'vmware':
        pytest.skip('Currently without publicly-facing VMware')

    cred = request.getfixturevalue(cred_fixture)
    inv_source = factories.v2_inventory_source(source=inv_source, credential=cred)
    return inv_source.ds.inventory


# Convenience fixture that returns all of our cloud_groups as a list
@pytest.fixture(scope="function")
def cloud_groups(aws_group, azure_group, azure_ad_group, gce_group, openstack_v2_group,
                 openstack_v3_group):  # TODO: Add VMware when possible
    return [aws_group, azure_group, azure_ad_group, gce_group, openstack_v2_group, openstack_v3_group]


# Convenience fixture that iterates through cloud_groups that support source_regions
@pytest.fixture(scope="function", params=['aws', 'azure', 'gce'])
def cloud_group_supporting_source_regions(request):
    return request.getfixturevalue(request.param + '_group')


@pytest.fixture
def inventory_script_code_with_sleep():
    def fn(sleep_time):
        return "#!/usr/bin/env python\nimport time\ntime.sleep({})\nprint('{{}}')\n".format(sleep_time)
    return fn
