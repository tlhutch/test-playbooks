import re
import logging
import pytest
import json
import uuid
import urllib2
import socket
import fauxfactory
import common.exceptions


log = logging.getLogger(__name__)


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


@pytest.fixture(scope="function")
def ansible_default_ipv4(request, ansible_facts):
    '''Return the ansible_default_ipv4 from ansible_facts of the system under test.'''
    if len(ansible_facts) > 1:
        log.warning("ansible_facts for %d systems found, but returning "
                    "only the first" % len(ansible_facts))
    return ansible_facts.values()[0]['ansible_facts']['ansible_default_ipv4']['address']


@pytest.fixture(scope="function")
def inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Random inventory - %s" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def another_inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Random inventory - %s" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def custom_inventory_update_with_status_completed(custom_inventory_source):
    '''
    Launches an inventory sync.
    '''
    # navigate to launch_pg and launch inventory update
    update_pg = custom_inventory_source.get_related('update')
    result = update_pg.post()

    # navigate to inventory_update page and check results
    inventory_updates_pg = custom_inventory_source.get_related('inventory_updates', id=result.json['inventory_update'])
    assert inventory_updates_pg.count == 1, "Unexpected number of updates returned (%s != 1)" % inventory_updates_pg.count

    inventory_update_pg = inventory_updates_pg.results[0].wait_until_completed()
    assert inventory_update_pg.is_successful, "Job unsuccessful - %s" % inventory_update_pg

    return inventory_update_pg


@pytest.fixture(scope="function")
def host_with_default_ipv4_in_variables(request, authtoken, api_hosts_pg, group, ansible_default_ipv4):
    '''Create a random inventory host where ansible_ssh_host == ansible_default_ipv4.'''
    payload = dict(name="random_host_alias-%s" % fauxfactory.gen_alphanumeric(),
                   description="host-%s" % fauxfactory.gen_utf8(),
                   variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local")),
                   inventory=group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def my_public_ipv4(request):
    '''
    Return the IP address of the system running pytest.

    NOTE: this doesn't work properly when the system running pytest and the
    target system are both on a private network.
    '''
    return json.load(urllib2.urlopen('http://httpbin.org/ip'))['origin']


@pytest.fixture(scope="function")
def local_ipv4_addresses(request):
    '''
    Return the list of ip addresses for the system running tests.
    '''
    return socket.gethostbyname_ex(socket.gethostname())[2]


@pytest.fixture(scope="function")
def hosts_with_name_matching_local_ipv4_addresses(request, authtoken, group, local_ipv4_addresses):
    '''Create an inventory host matching the public ipv4 address of the system running pytest.'''
    for ipv4_addr in local_ipv4_addresses:
        payload = dict(name=ipv4_addr,
                       description="test host %s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        obj = group.get_related('hosts').post(payload)
        request.addfinalizer(obj.silent_delete)
        # Add to group
        with pytest.raises(common.exceptions.NoContent_Exception):
            obj.get_related('groups').post(dict(id=group.id))

    return group.get_related('hosts', name__in=','.join(local_ipv4_addresses))


@pytest.fixture(scope="function")
def group(request, authtoken, api_groups_pg, inventory):
    payload = dict(name="group-%s" % fauxfactory.gen_alphanumeric(),
                   description="group description - %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
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
    request.addfinalizer(obj.silent_delete)
    # Add host to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def host_with_default_connection(request, authtoken, api_hosts_pg, inventory, group):
    payload = dict(name="localhost",
                   description="a non-random local host",
                   inventory=inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    # Add host to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def host_without_group(request, authtoken, inventory):
    payload = dict(name="random.host.%s" % fauxfactory.gen_alphanumeric(),
                   description="a host detached from any groups - %s" % fauxfactory.gen_utf8(),
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    obj = inventory.get_related('hosts').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def host(request, authtoken, api_hosts_pg, inventory, group):
    payload = dict(name="random.host.%s" % fauxfactory.gen_alphanumeric(),
                   description="random description - %s" % fauxfactory.gen_utf8(),
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    # Add host to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


#
# Inventory Scripts
#
@pytest.fixture(scope="function")
def script_source(request):

    # custom source_script supplied via pytest.mark.fixture_args(source_script=)
    fixture_args = getattr(request.function, 'fixture_args', None)
    if fixture_args and 'source_script' in fixture_args.kwargs:
        return fixture_args.kwargs['source_script']

    # create script to generate inventory
    group_name = re.sub(r"[\']", "", u"group-%s" % fauxfactory.gen_utf8())
    script = u'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
inventory = dict()
inventory['{0}'] = list()
'''.format(group_name)
    for i in range(5):
        host_name = re.sub(r"[\':]", "", u"host-%s" % fauxfactory.gen_utf8())
        script += u"inventory['{0}'].append('{1}')\n".format(group_name, host_name)
    script += u"print json.dumps(inventory)\n"
    log.debug(script)
    return script


@pytest.fixture(scope="function")
def inventory_script(request, authtoken, api_inventory_scripts_pg, script_source, organization):
    # build payload
    payload = dict(name="random_inventory_script-%s" % fauxfactory.gen_utf8(),
                   description="Random Inventory Script - %s" % fauxfactory.gen_utf8(),
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
    payload = dict(name="aws-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="AWS group %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=aws_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

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
    payload = dict(name="rax-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Rackspace group %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=rax_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

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
    payload = dict(name="azure-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Microsoft Azure %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=azure_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

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
    payload = dict(name="gce-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Google Compute Engine %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=gce_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

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
    payload = dict(name="vmware-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="VMware vCenter %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=vmware_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

    # Set the inventory_source.sourc = 'vmware'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='vmware', credential=vmware_credential.id)
    return obj


@pytest.fixture(scope="function")
def vmware_inventory_source(request, authtoken, vmware_group):
    return vmware_group.get_related('inventory_source')


#
# Openstack_v2 group
#
@pytest.fixture(scope="function")
def openstack_v2_group(request, authtoken, api_groups_pg, inventory, openstack_v2_credential):
    payload = dict(name="openstack-v2-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Openstack %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=openstack_v2_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

    # Set the inventory_source.sourc = 'openstack'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='openstack', credential=openstack_v2_credential.id)
    return obj


#
# Openstack_v3 group
#
@pytest.fixture(scope="function")
def openstack_v3_group(request, authtoken, api_groups_pg, inventory, openstack_v3_credential):
    payload = dict(name="openstack-v3-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Openstack %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   credential=openstack_v3_credential.id)
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

    # Set the inventory_source.sourc = 'openstack'
    inv_source = obj.get_related('inventory_source')
    inv_source.patch(source='openstack', credential=openstack_v3_credential.id)
    return obj


#
# Openstack group
#
@pytest.fixture(scope="function", params=['openstack_v2', 'openstack_v3'])
def openstack_group(request):
    return request.getfuncargvalue(request.param + '_group')


@pytest.fixture(scope="function")
def openstack_v2_inventory_source(request, authtoken, openstack_v2_group):
    return openstack_v2_group.get_related('inventory_source')


@pytest.fixture(scope="function")
def openstack_v3_inventory_source(request, authtoken, openstack_v3_group):
    return openstack_v3_group.get_related('inventory_source')


#
# Custom group
#
@pytest.fixture(scope="function")
def custom_group(request, authtoken, api_groups_pg, inventory, inventory_script):
    payload = dict(name="custom-group-%s" % fauxfactory.gen_alphanumeric(),
                   description="Custom Group %s" % fauxfactory.gen_utf8(),
                   inventory=inventory.id,
                   variables=json.dumps(dict(my_group_variable=True)))
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.silent_delete)

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
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware', 'openstack_v2', 'openstack_v3'])
def cloud_group(request):
    return request.getfuncargvalue(request.param + '_group')


#
# Convenience fixture that returns all of our cloud_groups as a list
#
@pytest.fixture(scope="function")
def cloud_groups(aws_group, rax_group, azure_group, gce_group, vmware_group, openstack_v2_group, openstack_v3_group):
    return [aws_group, rax_group, azure_group, gce_group, vmware_group, openstack_v2_group, openstack_v3_group]


#
# Convenience fixture that iterates through cloud_groups that support source_regions
#
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce'])
def cloud_group_supporting_source_regions(request):
    return request.getfuncargvalue(request.param + '_group')
