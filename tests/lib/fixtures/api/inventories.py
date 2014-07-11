import pytest
import json
import uuid
import urllib2
import random
import common.utils
import common.exceptions

@pytest.fixture(scope="function")
def random_ipv4(request):
    '''Return a randomly generated ipv4 address.'''
    return ".".join(str(random.randint(1, 255)) for i in range(4))


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


@pytest.fixture(scope="function")
def host_config_key():
    '''Returns a uuid4 string for use as a host_config_key.'''
    return str(uuid.uuid4())
