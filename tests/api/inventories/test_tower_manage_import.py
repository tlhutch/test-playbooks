import json

import fauxfactory
import pytest

from tests.api import Base_Api_Test


def inventory_dict():
    """Return inventory json to simulate an ec2 inventory import.  The ec2_id used
    is randomly generated.
    """
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
            "ec2_id": fauxfactory.gen_alphanumeric(),
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
        my_inventory['ipv6 hosts'].append(towerkit.utils.random_ipv6())
    return my_inventory


@pytest.fixture(scope="function")
def import_inventory(request, authtoken, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Random inventory - %s" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.mark.api
@pytest.mark.ha_tower
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Tower_Manage_Inventory_Import(Base_Api_Test):
    """Verify successful 'tower-manage inventory_import' operation.  This class
    tests import using both --inventory-id and --inventory-name.  Importing
    with, and without, available licenses is also confirmed.
    """

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_using_bad_id(self, ansible_runner, api_inventories_pg, import_inventory):
        """Verify that importing inventory using a bogus --inventory-id=<ID> fails"""
        # find an inventory_id that doesn't exist
        bad_id = towerkit.utils.random_int()
        while api_inventories_pg.get(id=bad_id).count != 0:
            bad_id = towerkit.utils.random_int()

        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-id %s --source /etc/fstab' % bad_id)
        # Verify the import failed
        for result in contacted.values():
            assert result['rc'] == 1, "tower-manage inventory_import succeeded " \
                "unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

    def test_import_bad_name(self, ansible_runner, import_inventory):
        """Verify that importing inventory using a bogus --inventory-name=<NAME> fails"""
        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name "%s" --source /etc/fstab' % fauxfactory.gen_alphanumeric())
        # Verify the import failed
        for result in contacted.values():
            assert result['rc'] == 1, "tower-manage inventory_import succeeded " \
                "unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

    def test_import_by_id(self, ansible_runner, import_inventory):
        """Verify that importing inventory using --inventory-id=<ID> succeeds"""
        # Upload inventory script
        dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-id %s --source %s' % (import_inventory.id, dest))
        # Verify the import completed successfully
        for result in contacted.values():
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_by_name(self, ansible_runner, import_inventory):
        """Verify that importing inventory using --inventory-name=<NAME> succeeds"""
        # Upload inventory script
        dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, dest))

        for result in contacted.values():
            # Verify the import completed successfully
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_ini(self, ansible_runner, import_inventory):
        """Verify that importing inventory from a .INI file succeeds"""
        # Upload inventory script
        dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=10, ini=True)

        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, dest))

        for result in contacted.values():
            # Verify the import completed successfully
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    # The following test was disabled as it did not consistently pass.  I'm not
    # convinced this makes a great test considering timing can vary based on a
    # variety of factors.
    def FIXME_test_import_multiple(self, ansible_runner, import_inventory):
        """Verify that multiple imports of the same inventory are subsequently are faster"""
        # Upload inventory script
        dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=100, ini=True)

        # Run first tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, dest))
        for result in contacted.values():
            # Verify the import completed successfully
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

            # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
            (hours, minutes, seconds) = result['delta'].split(':')
            first_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 100

        # Run second tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name %s --source %s --overwrite' % (import_inventory.name, dest))
        for result in contacted.values():
            # Verify the import completed successfully
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

            # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
            (hours, minutes, seconds) = result['delta'].split(':')
            second_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        # Run third tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-name %s --source %s' % (import_inventory.name, dest))
        for result in contacted.values():
            # Verify the import completed successfully
            assert result['rc'] == 0, "tower-manage inventory_import " \
                "failed:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

            # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
            (hours, minutes, seconds) = result['delta'].split(':')
            third_import = float(seconds) + 60 * float(minutes) + 60 * 60 * float(hours)

        # assert subsequent imports were faster
        assert first_import > second_import > third_import, \
            "Unexpected timing when importing inventory multiple times: %s, %s, %s" % \
            (first_import, second_import, third_import)

    def test_import_license_exceeded(self, api_config_pg, ansible_runner, import_inventory):
        """Verify inventory_import fails if the number of imported hosts will exceed licensed amount"""
        # update test license
        api_config_pg.install_license(1000)

        # Upload inventory script
        dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=2000)

        # Run tower-manage inventory_import
        contacted = ansible_runner.shell('tower-manage inventory_import --inventory-id %s --source %s' % (import_inventory.id, dest))
        for result in contacted.values():
            # Verify the import failed
            assert result['rc'] == 1, "tower-manage inventory_import " \
                "succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
                % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count == 0
        assert import_inventory.get_related('hosts').count == 0

    def test_import_instance_id_constraint(self, ansible_runner, import_inventory, json_inventory_before, json_inventory_after, tower_version_cmp):
        """Verify that tower can handle inventory_import where the host name
        remains the same, but the instance_id changes.
        """
        if tower_version_cmp('2.0.2') < 0:
            pytest.xfail("Only supported on tower-2.0.2 (or newer)")

        # Copy inventory_before to test system
        contacted = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(json_inventory_before, indent=4),))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: %s" % result

        # Import inventory_before
        cmd = "tower-manage inventory_import --inventory-id %s --instance-id-var ec2_id " \
            "--source /tmp/inventory.sh" % import_inventory.id
        contacted = ansible_runner.command(cmd)
        for result in contacted.values():
            assert result['rc'] == 0, "tower-manage inventory_import failed: %s" % json.dumps(result, indent=2)
            print result

        # Copy inventory_after to test system
        contacted = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(json_inventory_after, indent=4),))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: %s" % result

        # Import inventory_after
        cmd = "tower-manage inventory_import --inventory-id %s --instance-id-var ec2_id " \
            "--source /tmp/inventory.sh" % import_inventory.id
        contacted = ansible_runner.command(cmd)
        for result in contacted.values():
            assert result['rc'] == 0, "tower-manage inventory_import failed: %s" % json.dumps(result, indent=2)
            print result

    def test_import_ipv6_hosts(self, ansible_runner, import_inventory, json_inventory_ipv6, tower_version_cmp):
        """Verify that tower can handle inventory_import with ipv6 hosts."""
        if tower_version_cmp('2.0.2') < 0:
            pytest.xfail("Only supported on tower-2.0.2 (or newer)")

        # Copy inventory_before to test system
        contacted = ansible_runner.copy(dest='/tmp/inventory.sh', mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(json_inventory_ipv6, indent=4),))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: %s" % result

        # Import inventory_before
        cmd = "tower-manage inventory_import --inventory-id %s --source /tmp/inventory.sh" % import_inventory.id
        contacted = ansible_runner.command(cmd)
        for result in contacted.values():
            assert result['rc'] == 0, "tower-manage inventory_import failed: %s" % json.dumps(result, indent=2)
            print result

    @pytest.mark.skipif(True, reason="TODO - https://trello.com/c/JF0hVue0")
    def test_import_directory(self, ansible_runner, import_inventory):
        """Verify that tower can handle inventory_import when --source refers a
        directory.
        """
        pass
