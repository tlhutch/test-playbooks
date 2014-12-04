import pytest
import json
import uuid
import urllib2
import common.utils
import common.exceptions


@pytest.fixture(scope="function")
def api_inventory_sources_options_json(request, authtoken, api_inventory_sources_pg):
    '''Return inventory_sources OPTIONS json.'''
    return api_inventory_sources_pg.options().json


#
# Various choices values from the OPTIONS request
#
@pytest.fixture(scope="function")
def azure_region_choices(request, api_inventory_sources_options_json):
    '''Return field 'azure_ret_choices' from the inventory_sources OPTIONS json.'''
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['azure_region_choices'])


@pytest.fixture(scope="function")
def gce_region_choices(request, api_inventory_sources_options_json):
    '''Return field 'gce_ret_choices' from the inventory_sources OPTIONS json.'''
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['gce_region_choices'])


@pytest.fixture(scope="function")
def ec2_region_choices(request, api_inventory_sources_options_json):
    '''Return field 'ec2_ret_choices' from the inventory_sources OPTIONS json.'''
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['ec2_region_choices'])


@pytest.fixture(scope="function")
def rax_region_choices(request, api_inventory_sources_options_json):
    '''Return field 'rax_ret_choices' from the inventory_sources OPTIONS json.'''
    return dict(api_inventory_sources_options_json['actions']['GET']['source_regions']['rax_region_choices'])


@pytest.fixture(scope="function")
def ec2_group_by_choices(request, api_inventory_sources_options_json):
    '''Return field 'ec2_group_by_choices' from the inventory_sources OPTIONS json.'''
    return dict(api_inventory_sources_options_json['actions']['GET']['group_by']['ec2_group_by_choices'])


@pytest.fixture(scope="function")
def host_config_key():
    '''Returns a uuid4 string for use as a host_config_key.'''
    return str(uuid.uuid4())


@pytest.fixture(scope="class")
def ansible_default_ipv4(request, ansible_facts):
    '''Return the ansible_default_ipv4 from ansible_facts of the system under test.'''
    return ansible_facts['ansible_default_ipv4']['address']


@pytest.fixture(scope="function")
def inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def host_ipv4(request, authtoken, api_hosts_pg, group, ansible_default_ipv4):
    '''Create a random inventory host where ansible_ssh_host == ansible_default_ipv4.'''
    payload = dict(name="random_host_alias - %s" % common.utils.random_ascii(),
                   description="host-%s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local")),
                   inventory=group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def my_public_ipv4(request):
    '''Return the IP address of the system running pytest'''
    return json.load(urllib2.urlopen('http://httpbin.org/ip'))['origin']


@pytest.fixture(scope="function")
def host_public_ipv4(request, authtoken, api_hosts_pg, group, my_public_ipv4):
    '''Create an inventory host matching the public ipv4 address of the system running pytest.'''
    payload = dict(name=my_public_ipv4,
                   description="test host %s" % common.utils.random_unicode(),
                   inventory=group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def group(request, authtoken, api_groups_pg, inventory):
    payload = dict(name="group-%s" % common.utils.random_ascii(),
                   description="group description - %s" % common.utils.random_unicode(),
                   inventory=inventory.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def inventory_source(request, authtoken, group):
    return group.get_related('inventory_source')


@pytest.fixture(scope="function")
def host_local(request, authtoken, api_hosts_pg, inventory, group):
    payload = dict(name="local",
                   description="a non-random local host",
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add host to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def host_without_group(request, authtoken, inventory):
    payload = dict(name="random.host.%s" % common.utils.random_ascii(),
                   description="a host detached from any groups - %s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    obj = inventory.get_related('hosts').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def host(request, authtoken, api_hosts_pg, inventory, group):
    payload = dict(name="random.host.%s" % common.utils.random_ascii(),
                   description="random description - %s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add host to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


#
# Inventory Scripts
#
@pytest.fixture(scope="function")
def script_source(request):
    # support overriding the script_source via a pytest marker
    script = getattr(request.function, 'script_source', None)
    if script is not None:
        return script.args[0]

    # create script to generate inventory
    group_name = u"group-%s" % common.utils.random_unicode().replace("'", "")
    script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
inventory = dict()
inventory['{0}'] = list()
'''.format(group_name)
    for i in range(5):
        script += "inventory['{0}'].append('host-{1}')\n".format(group_name, common.utils.random_unicode().replace("'", ""))
    script += "print json.dumps(inventory)\n"
    return script


@pytest.fixture(scope="function")
def inventory_script(request, authtoken, api_inventory_scripts_pg, script_source, organization):
    # build payload
    payload = dict(name="random_inventory_script-%s" % common.utils.random_unicode(),
                   description="Random Inventory Script - %s" % common.utils.random_unicode(),
                   organization=organization.id,
                   script=script_source)
    obj = api_inventory_scripts_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


#
# Amazon AWS group
#
@pytest.fixture(scope="function")
def aws_group(request, authtoken, api_groups_pg, inventory, aws_credential):
    payload = dict(name="aws-group-%s" % common.utils.random_ascii(),
                   description="AWS group %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   credential=aws_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'ec2'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='ec2', credential=aws_credential.id)
    return obj


@pytest.fixture(scope="function")
def aws_inventory_source(request, authtoken, aws_group):
    return aws_group.get_related('inventory_source')


#
# Rackspace group
#
@pytest.fixture(scope="function")
def rax_group(request, authtoken, api_groups_pg, inventory, rax_credential):
    payload = dict(name="rax-group-%s" % common.utils.random_ascii(),
                   description="Rackspace group %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   credential=rax_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'rax'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='rax', credential=rax_credential.id)
    return obj


@pytest.fixture(scope="function")
def rax_inventory_source(request, authtoken, rax_group):
    return rax_group.get_related('inventory_source')


#
# Azure group
#
@pytest.fixture(scope="function")
def azure_group(request, authtoken, api_groups_pg, inventory, azure_credential):
    payload = dict(name="azure-group-%s" % common.utils.random_ascii(),
                   description="Microsoft Azure %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   credential=azure_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'azure'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='azure', credential=azure_credential.id)
    return obj


@pytest.fixture(scope="function")
def azure_inventory_source(request, authtoken, azure_group):
    return azure_group.get_related('inventory_source')


#
# GCE group
#
@pytest.fixture(scope="function")
def gce_group(request, authtoken, api_groups_pg, inventory, gce_credential):
    payload = dict(name="gce-group-%s" % common.utils.random_ascii(),
                   description="Google Compute Engine %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   credential=gce_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'gce'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='gce', credential=gce_credential.id)
    return obj


@pytest.fixture(scope="function")
def gce_inventory_source(request, authtoken, gce_group):
    return gce_group.get_related('inventory_source')


#
# VMware group
#
@pytest.fixture(scope="function")
def vmware_group(request, authtoken, api_groups_pg, inventory, vmware_credential):
    payload = dict(name="vmware-group-%s" % common.utils.random_ascii(),
                   description="VMware vCenter %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   credential=vmware_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source.sourc = 'vmware'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='vmware', credential=vmware_credential.id)
    return obj


@pytest.fixture(scope="function")
def vmware_inventory_source(request, authtoken, vmware_group):
    return vmware_group.get_related('inventory_source')


#
# Custom group
#
@pytest.fixture(scope="function")
def custom_group(request, authtoken, api_groups_pg, inventory, inventory_script):
    payload = dict(name="custom-group-%s" % common.utils.random_ascii(),
                   description="Custom Group %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   variables=json.dumps(dict(my_group_variable=True)))
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Set the inventory_source
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='custom',
                     source_script=inventory_script.id)
    return obj


@pytest.fixture(scope="function")
def custom_inventory_source(request, authtoken, custom_group):
    return custom_group.get_related('inventory_source')


#
# Convenience fixture that iterates through supported cloud_groups
#
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware'])
def cloud_group(request):
    return request.getfuncargvalue(request.param + '_group')
