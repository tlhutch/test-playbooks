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
    return factories.v2_inventory(organization=organization, localhost=None)


@pytest.fixture(scope="function")
def another_inventory(factories, organization):
    return factories.v2_inventory(organization=organization, localhost=None)


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
    inventory = factories.v2_inventory(
        organization=organization,
        variables=json.dumps(dict(ansible_connection="local"))
    )
    return factories.v2_inventory_source(inventory=inventory, source_script=inventory_script)


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

    group_name = re.sub(r"[\']", "", "group_%s" % fauxfactory.gen_utf8())
    script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
inventory = dict()
inventory['{0}'] = list()
""".format(group_name)
    for i in range(5):
        host_name = re.sub(r"[\':]", "", "host_%s" % fauxfactory.gen_utf8())
        script += "inventory['{0}'].append('{1}')\n".format(group_name, host_name)
    script += "print(json.dumps(inventory))\n"
    log.debug(script)
    return script


@pytest.fixture(scope="function")
def inventory_script(factories, script_source, organization):
    return factories.v2_inventory_script(organization=organization, script=script_source)


@pytest.fixture(scope="function")
def aws_inventory_source(factories, aws_credential):
    return factories.v2_inventory_source(credential=aws_credential, source='ec2')


@pytest.fixture(scope="function")
def aws_inventory_hostvars():
    return {
        "ansible_host": "",
        "ec2_account_id": "",
        "ec2_ami_launch_index": "",
        "ec2_architecture": "",
        "ec2_block_devices": "",
        "ec2_client_token": "",
        "ec2_dns_name": "",
        "ec2_ebs_optimized": "",
        "ec2_group_name": "",
        "ec2_hypervisor": "",
        "ec2_id": "",
        "ec2_image_id": "",
        "ec2_instance_type": "",
        "ec2_ip_address": "",
        "ec2_kernel": "",
        "ec2_launch_time": "",
        "ec2_monitored": "",
        "ec2_monitoring_state": "",
        "ec2_placement": "",
        "ec2_platform": "",
        "ec2_private_dns_name": "",
        "ec2_private_ip_address": "",
        "ec2_public_dns_name": "",
        "ec2_ramdisk": "",
        "ec2_reason": "",
        "ec2_region": "",
        "ec2_root_device_name": "",
        "ec2_root_device_type": "",
        "ec2_security_group_ids": "",
        "ec2_security_group_names": "",
        "ec2_sourceDestCheck": "",
        "ec2_state": "",
        "ec2_state_code": "",
        "ec2_subnet_id": "",
        "ec2_virtualization_type": "",
        "ec2_vpc_id": "",
        }


@pytest.fixture(scope="function")
def azure_inventory_hostvars():
    return {
        "ansible_host": "",
        "computer_name": "",
        "id": "",
        "image": "",
        "location": "",
        "mac_address": "",
        "name": "",
        "network_interface": "",
        "network_interface_id": "",
        "os_disk": "",
        "plan": "",
        "powerstate": "",
        "private_ip": "",
        "provisioning_state": "",
        "public_ip": "",
        "public_ip_id": "",
        "public_ip_name": "",
        "resource_group": "",
        "security_group": "",
        "security_group_id": "",
        "tags": "",
        "type": "",
        "virtual_machine_size": "",
    }


@pytest.fixture(scope="function")
def gce_inventory_hostvars():
    return {
        "ansible_ssh_host": "",
        "gce_id": "",
        "gce_image": "",
        "gce_machine_type": "",
        "gce_metadata": "",
        "gce_name": "",
        "gce_network": "",
        "gce_private_ip": "",
        "gce_public_ip": "",
        "gce_status": "",
        "gce_subnetwork": "",
        "gce_tags": "",
        # "gce_uuid": "", not recoverable, was artifact of libcloud
        "gce_zone": "",
    }


@pytest.fixture(scope="function")
def openstack_inventory_hostvars():
    return {
        "ansible_host": "",
        "ansible_ssh_host": "",
        "openstack": {
            "OS-DCF:diskConfig": "",
            "OS-EXT-AZ:availability_zone": "",
            "OS-EXT-STS:power_state": "",
            "OS-EXT-STS:task_state": "",
            "OS-EXT-STS:vm_state": "",
            "OS-SRV-USG:launched_at": "",
            "OS-SRV-USG:terminated_at": "",
            "accessIPv4": "",
            "accessIPv6": "",
            "addresses": "",
            "adminPass": "",
            "az": "",
            "cloud": "",
            "config_drive": "",
            "created": "",
            "disk_config": "",
            "flavor": "",
            "has_config_drive": "",
            "hostId": "",
            "host_id": "",
            "id": "",
            "image": "",
            "interface_ip": "",
            "key_name": "",
            "launched_at": "",
            "location": "",
            "metadata": "",
            "name": "",
            "networks": "",
            "os-extended-volumes:volumes_attached": "",
            "power_state": "",
            "private_v4": "",
            "progress": "",
            "project_id": "",
            "properties": {
                "OS-DCF:diskConfig": "",
                "OS-EXT-AZ:availability_zone": "",
                "OS-EXT-STS:power_state": "",
                "OS-EXT-STS:task_state": "",
                "OS-EXT-STS:vm_state": "",
                "OS-SRV-USG:launched_at": "",
                "OS-SRV-USG:terminated_at": "",
                "os-extended-volumes:volumes_attached": "",
            },
            "public_v4": "",
            "public_v6": "",
            "region": "",
            "security_groups": "",
            "status": "",
            "task_state": "",
            "tenant_id": "",
            "terminated_at": "",
            "updated": "",
            "user_id": "",
            "vm_state": "",
            "volumes": "",
    }
    }


@pytest.fixture(scope="function")
def cloud_inventory_hostvars(azure_inventory_hostvars, gce_inventory_hostvars, aws_inventory_hostvars, openstack_inventory_hostvars):
    """Return map to each inventory type's expected hostvars when run in compatibility mode.

    These are what we consider a minimum acceptable set of hostvars that each host should have defined.
    """
    return {
        'ec2': aws_inventory_hostvars,
        'azure_rm': azure_inventory_hostvars,
        'gce': gce_inventory_hostvars,
        'openstack': openstack_inventory_hostvars,
        }


@pytest.fixture(scope="function")
def aws_inventory_hostgroups():
    return {
        "zones": "",
        "security_groups": "",
        "ec2": "",
        "regions": "",
        "platforms": "",
        "tags": "",
        "vpcs": "",
    }


@pytest.fixture(scope="function")
def azure_inventory_hostgroups():
    return {
        "azure": "",
        "eastus": "",
        "linux": "",
    }


@pytest.fixture(scope="function")
def gce_inventory_hostgroups():
    return {
        "status_running": "",
    }


@pytest.fixture(scope="function")
def openstack_inventory_hostgroups():
    return {
        "devstack": "",
        "nova": "",
    }


def _emulate_core_sanitization(s):
    result = ""
    for letter in s:
        if letter == ' ':
            result += '_'
        elif ord(letter) < 128:
            result += letter
        else:
            result += '_'

    return result


@pytest.fixture(scope="function")
def cloud_hostvars_that_create_groups():
    return {
        'ec2': {
                'ec2_placement': lambda x: x,
                'ec2_region': lambda x: x,
                'ec2_vpc_id': lambda x: 'vpc_id_{}'.format('_'.join([word for word in x.split('-')])),
                'ec2_security_group_names': lambda x: 'security_group_{}'.format('_'.join([word for word in x.split('-')])),
               },
        'gce': {
                   'gce_zone': lambda x: x,
                   'gce_status': lambda x: 'status_{}'.format(x.lower()),
                   'gce_tags': lambda x: f'tag_{x}',
               },

        'azure_rm': {
                # note this is only if these are enabled via source vars
                'tags': lambda x: '_'.join(_emulate_core_sanitization(word) for word in x.split()),
               }
        }


@pytest.fixture(scope="function")
def cloud_hostvars_that_create_host_names():
    return {
        'ec2': ['ec2_ip_address', 'ec2_dns_name'],
        'gce': ['gce_name'],
        'azure_rm': ['computer_name']  # also name
    }


@pytest.fixture(scope="function")
def cloud_inventory_hostgroups(azure_inventory_hostgroups, gce_inventory_hostgroups, aws_inventory_hostgroups, openstack_inventory_hostgroups):
    """Return map to each inventory type's expected groups created when run in compatibility mode.

    These are what we consider a minimum acceptable set of groups that each inventory should create on import.

    Note these groups are generated dynamically from values in hostvars, so our expectations are pretty low
    and still could be effected by changes in the environment.

    If a test began to fail because of these groups missing, it would also be prudent to look to see if the
    hostvar that would provide the data is present.
    """
    return {
        'ec2': aws_inventory_hostgroups,
        'azure_rm': azure_inventory_hostgroups,
        'gce': gce_inventory_hostgroups,
        'openstack': openstack_inventory_hostgroups,
        }


@pytest.fixture(scope="function")
def azure_inventory_source(factories, azure_credential):
    return factories.v2_inventory_source(credential=azure_credential, source='azure_rm')


@pytest.fixture(scope="function")
def gce_inventory_source(factories, gce_credential):
    return factories.v2_inventory_source(credential=gce_credential, source='gce')


@pytest.fixture(scope="function")
def vmware_inventory_source(vmware_credential):
    pytest.skip('Currently without access to functional VMware system')


@pytest.fixture(scope="function")
def openstack_inventory_source(factories, openstack_credential):
    return factories.v2_inventory_source(source='openstack', credential=openstack_credential)


@pytest.fixture(scope="function")
def custom_inventory_source(request, authtoken, inventory_source):
    return inventory_source.get()


@pytest.fixture(scope="function", params=['aws', 'azure', 'gce', 'vmware', 'openstack'])
def cloud_inventory_source(request):
    return request.getfixturevalue(request.param + '_inventory_source')


@pytest.fixture(scope="function", params=[('ec2', 'aws_credential'),
                                          ('azure_rm', 'azure_credential'),
                                          ('gce', 'gce_credential'),
                                          ('vmware', 'vmware_credential'),
                                          ('openstack', 'openstack_credential')
    ], ids=['aws', 'azure', 'gce', 'vmware', 'openstack'])
def cloud_inventory(request, factories):
    inv_source, cred_fixture = request.param
    if inv_source == 'vmware':
        pytest.skip('Currently without publicly-facing VMware')

    cred = request.getfixturevalue(cred_fixture)
    inv_source = factories.v2_inventory_source(source=inv_source, credential=cred)
    return inv_source.ds.inventory


# Convenience fixture that iterates through cloud_groups that support source_regions
@pytest.fixture(scope="function", params=['aws', 'azure', 'gce'])
def cloud_inventory_source_supporting_source_regions(request):
    return request.getfixturevalue(request.param + '_inventory_source')


@pytest.fixture
def inventory_script_code_with_sleep():
    def fn(sleep_time):
        return "#!/usr/bin/env python\nimport time\ntime.sleep({})\nprint('{{}}')\n".format(sleep_time)
    return fn
