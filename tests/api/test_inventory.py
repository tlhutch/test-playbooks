import json
import pytest
import logging
import common.tower.inventory
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


def inventory_dict():
    '''
    Return inventory json to simulate an ec2 inventory import.  The ec2_id used
    is randomly generated.
    '''
    return {  # NOQA
      "_meta": {
        "hostvars": {
          "ec2.amazonaws.com": {
            "ec2__in_monitoring_element": False,
            "ec2_ami_launch_index": "0",
            "ec2_architecture": "x86_64",
            "ec2_client_token": "",
            "ec2_dns_name": "ec2.amazonaws.com",
            "ec2_ebs_optimized": False,
            "ec2_eventsSet": "",
            "ec2_group_name": "",
            "ec2_hypervisor": "xen",
            "ec2_id": common.utils.random_ascii(),
            "ec2_image_id": "ami-eb6b0182",
            "ec2_instance_profile": "",
            "ec2_instance_type": "m1.small",
            "ec2_ip_address": "107.20.56.8",
            "ec2_item": "",
            "ec2_kernel": "aki-88aa75e1",
            "ec2_key_name": "djohnson",
            "ec2_launch_time": "2014-09-30T11:57:56.000Z",
            "ec2_monitored": False,
            "ec2_monitoring": "",
            "ec2_monitoring_state": "disabled",
            "ec2_persistent": False,
            "ec2_placement": "us-east-1c",
            "ec2_platform": "",
            "ec2_previous_state": "",
            "ec2_previous_state_code": 0,
            "ec2_private_dns_name": "ip-10-190-219-123.ec2.internal",
            "ec2_private_ip_address": "10.190.219.123",
            "ec2_public_dns_name": "ec2.amazonaws.com",
            "ec2_ramdisk": "",
            "ec2_reason": "",
            "ec2_region": "us-east-1",
            "ec2_requester_id": "",
            "ec2_root_device_name": "/dev/sda1",
            "ec2_root_device_type": "ebs",
            "ec2_security_group_ids": "sg-b05be0db",
            "ec2_security_group_names": "default",
            "ec2_spot_instance_request_id": "",
            "ec2_state": "running",
            "ec2_state_code": 16,
            "ec2_state_reason": "",
            "ec2_subnet_id": "",
            "ec2_tag_ansible_group": "dbservers",
            "ec2_tag_group": "default",
            "ec2_tag_type": "m1.small",
            "ec2_virtualization_type": "paravirtual",
            "ec2_vpc_id": ""
          }
        }
      },
      "ec2": [
        "ec2.amazonaws.com"
      ],
    }


@pytest.fixture(scope="function")
def json_inventory_before(request):
    return inventory_dict()


@pytest.fixture(scope="function")
def json_inventory_after(request):
    return inventory_dict()


@pytest.fixture(scope="function")
def json_inventory_ipv6(request):
    my_inventory = {  # NOQA
      "_meta": {
        "hostvars": {}
      },
      "ipv6 hosts": [],
    }

    # Add 10 random ipv6 hosts
    for i in range(10):
        my_inventory['ipv6 hosts'].append(common.utils.random_ipv6())
    return my_inventory


@pytest.fixture(scope="function")
def import_inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_host_without_group(self, ansible_runner, host_without_group, tower_version_cmp):
        '''
        Verify that /inventory/N/script includes hosts that are not a member of
        any group.
            1) Create inventory with hosts, but no groups
            2) Verify the hosts appear in related->hosts
            2) Verify the hosts appear in related->script

        Trello: https://trello.com/c/kDdqEaOW
        '''

        if tower_version_cmp('2.0.0') < 0:
            pytest.xfail("Only supported on tower-2.0.0 (or newer)")

        inventory_pg = host_without_group.get_related('inventory')

        # Verify /groups is empty
        assert inventory_pg.get_related('groups').count == 0, \
            "Inventory unexpectedly has groups (%s)" % inventory_pg.get_related('groups').count
        # Verify /root_groups is empty
        assert inventory_pg.get_related('root_groups').count == 0, \
            "Inventory unexpectedly has root_groups (%s)" % inventory_pg.get_related('root_groups').count

        all_hosts = inventory_pg.get_related('hosts')
        assert all_hosts.count == 1

        script = inventory_pg.get_related('script').json
        script_all_hosts = len(script['all']['hosts'])

        assert all_hosts.count == script_all_hosts, \
            "The number of inventory hosts differs between endpoints " \
            "/hosts (%s) and /script (%s)" % (all_hosts.count, script_all_hosts)

    def test_cascade_delete(self, ansible_runner, inventory, host_local, host_without_group, group, api_groups_pg, api_hosts_pg):
        '''Verify DELETE removes associated groups and hosts'''

        # Verify inventory group/host counts
        assert inventory.get_related('groups').count == 1
        assert inventory.get_related('hosts').count == 2

        # Delete the inventory
        inventory.delete()

        # Related resources should be forbidden
        with pytest.raises(common.exceptions.Forbidden_Exception):
            inventory.get_related('groups')

        # Using main endpoint, find any matching groups
        groups_pg = api_groups_pg.get(id=inventory.id)

        # Assert no matching groups found
        assert groups_pg.count == 0, "ERROR: not All inventory groups were deleted"

        # Related resources should be forbidden
        with pytest.raises(common.exceptions.Forbidden_Exception):
            inventory.get_related('hosts')

        # Using main endpoint, find any matching hosts
        hosts_pg = api_hosts_pg.get(id=inventory.id)

        # Assert no matching hosts found
        assert hosts_pg.count == 0, "ERROR: not all inventory hosts were deleted"


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Tower_Manage_Inventory_Import(Base_Api_Test):
    '''
    Verify successful 'awx-manage inventory_import' operation.  This class
    tests import using both --inventory-id and --inventory-name.  Importing
    with, and without, available licenses is also confirmed.
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_using_bad_id(self, ansible_runner, api_inventories_pg, import_inventory):
        '''Verify that importing inventory using a bogus --inventory-id=<ID> fails'''

        # find an inventory_id that doesn't exist
        bad_id = common.utils.random_int()
        while api_inventories_pg.get(id=bad_id).count != 0:
            bad_id = common.utils.random_int()

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source /etc/fstab' % bad_id)
        logging.info(result['stdout'])

        # Verify the import failed
        assert result['rc'] == 1, "awx-manage inventory_import succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

    def test_import_bad_name(self, ansible_runner, import_inventory):
        '''Verify that importing inventory using a bogus --inventory-name=<NAME> fails'''

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name "%s" --source /etc/fstab' % common.utils.random_ascii())
        logging.info(result['stdout'])

        # Verify the import failed
        assert result['rc'] == 1, "awx-manage inventory_import succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

    def test_import_by_id(self, ansible_runner, import_inventory):
        '''Verify that importing inventory using --inventory-id=<ID> succeeds'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' % (import_inventory.id, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_by_name(self, ansible_runner, import_inventory):
        '''Verify that importing inventory using --inventory-name=<NAME> succeeds'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_ini(self, ansible_runner, import_inventory):
        '''Verify that importing inventory from a .INI file succeeds'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10, ini=True)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_multiple(self, ansible_runner, import_inventory):
        '''Verify that multiple imports of the same inventory are subsequently are faster'''
        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=100, ini=True)

        # Run first awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 100

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        first_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        # Run second awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s --overwrite' % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        second_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        # Run third awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        third_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        assert first_import > second_import > third_import, \
            "Unexpected timing when importing inventory multiple times: %s, %s, %s" % \
            (first_import, second_import, third_import)

    def test_import_license_exceeded(self, ansible_runner, import_inventory):
        '''Verify inventory_import fails if the number of imported hosts will exceed licensed amount'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=2000)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' % (import_inventory.id, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import failed
        assert result['rc'] == 1, "awx-manage inventory_import succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count == 0
        assert import_inventory.get_related('hosts').count == 0

    def test_import_instance_id_constraint(self, ansible_runner, import_inventory, json_inventory_before, json_inventory_after, tower_version_cmp):
        '''
        Verify that tower can handle inventory_import where the host name
        remains the same, but the instance_id changes.

        Verify https://trello.com/c/QWnujT3v
        '''

        if tower_version_cmp('2.0.2') < 0:
            pytest.xfail("Only supported on tower-2.0.2 (or newer)")

        # Copy inventory_before to test system
        result = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content='''#!/bin/bash
cat <<EOF
%s
EOF''' % (json.dumps(json_inventory_before, indent=4),))
        assert 'failed' not in result, "Failed to create inventory file: %s" % result

        # Import inventory_before
        cmd = "awx-manage inventory_import --inventory-id %s --instance-id-var ec2_id " \
            "--source /tmp/inventory.sh" % import_inventory.id
        result = ansible_runner.command(cmd)
        assert result['rc'] == 0, "awx-managed inventory_import failed: %s" % json.dumps(result, indent=2)
        print result

        # Copy inventory_after to test system
        result = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content='''#!/bin/bash
cat <<EOF
%s
EOF''' % (json.dumps(json_inventory_after, indent=4),))
        assert 'failed' not in result, "Failed to create inventory file: %s" % result

        # Import inventory_after
        cmd = "awx-manage inventory_import --inventory-id %s --instance-id-var ec2_id " \
            "--source /tmp/inventory.sh" % import_inventory.id
        result = ansible_runner.command(cmd)
        assert result['rc'] == 0, "awx-managed inventory_import failed: %s" % json.dumps(result, indent=2)
        print result

    def test_import_ipv6_hosts(self, ansible_runner, import_inventory, json_inventory_ipv6, tower_version_cmp):
        '''
        Verify that tower can handle inventory_import with ipv6 hosts.

        Trello: https://trello.com/c/ZBHrkuLb
        '''

        if tower_version_cmp('2.0.2') < 0:
            pytest.xfail("Only supported on tower-2.0.2 (or newer)")

        # Copy inventory_before to test system
        result = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content='''#!/bin/bash
cat <<EOF
%s
EOF''' % (json.dumps(json_inventory_ipv6, indent=4),))
        assert 'failed' not in result, "Failed to create inventory file: %s" % result

        # Import inventory_before
        cmd = "awx-manage inventory_import --inventory-id %s --source /tmp/inventory.sh" % import_inventory.id
        result = ansible_runner.command(cmd)
        assert result['rc'] == 0, "awx-managed inventory_import failed: %s" % json.dumps(result, indent=2)
        print result

    @pytest.mark.skipif(True, reason="TODO - https://trello.com/c/JF0hVue0")
    def test_import_directory(self, ansible_runner, import_inventory):
        '''
        Verify that tower can handle inventory_import when --source refers a
        directory.
        '''
