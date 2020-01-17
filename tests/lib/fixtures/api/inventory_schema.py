import logging

import pytest


log = logging.getLogger(__name__)


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
def inventory_hostvars(azure_inventory_hostvars, gce_inventory_hostvars, aws_inventory_hostvars, openstack_inventory_hostvars):
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
def hostvars_that_create_groups():
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
def hostvars_that_create_host_names():
    return {
        'ec2': ['ec2_ip_address', 'ec2_dns_name'],
        'gce': ['gce_name'],
        'azure_rm': ['computer_name']  # also name
    }


@pytest.fixture(scope="function")
def inventory_hostgroups(azure_inventory_hostgroups, gce_inventory_hostgroups, aws_inventory_hostgroups, openstack_inventory_hostgroups):
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
