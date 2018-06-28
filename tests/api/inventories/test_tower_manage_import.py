import json

from towerkit.tower.inventory import upload_inventory
from towerkit import utils
import fauxfactory
import pytest

from tests.api import Base_Api_Test


def get_ec2_inventory():
    """Return inventory JSON with randomly generated ec2_id."""
    return {
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


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_openshift
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestTowerManageInventoryImport(Base_Api_Test):

    def test_unrecognized_id(self, ansible_runner, inventory):
        """Verify failed import with unrecognized '--inventory-id' value."""
        random_id = utils.random_int()
        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source /etc/fstab'.format(random_id))

        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected awx-manage inventory_import success." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
        assert result['stderr'] == 'CommandError: Inventory with id = {0} cannot be found'.format(random_id)

    def test_unrecognized_name(self, ansible_runner, inventory):
        """Verify failed import with unrecognized '--inventory-name' value."""
        random_name = fauxfactory.gen_alphanumeric()
        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-name "{0}" --source /etc/fstab'.format(random_name))

        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected awx-manage inventory_import success." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
        assert result['stderr'] == 'CommandError: Inventory with name = {0} cannot be found'.format(random_name)

    def test_import_by_id(self, ansible_runner, inventory):
        """Verify successful import by inventory ID."""
        dest = upload_inventory(ansible_runner, nhosts=10)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])

        assert inventory.get_related('groups').count == 13
        assert inventory.get_related('hosts').count == 10

    def test_import_by_name(self, ansible_runner, inventory):
        """Verify successful import by inventory name."""
        dest = upload_inventory(ansible_runner, nhosts=10)

        contacted = ansible_runner.shell(u'awx-manage inventory_import --inventory-name "{0}" --source {1}'.format(inventory.name, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])

        assert inventory.get_related('groups').count == 13
        assert inventory.get_related('hosts').count == 10

    def test_import_with_ini_file(self, ansible_runner, inventory):
        """Verify successful import using an .INI file."""
        dest = upload_inventory(ansible_runner, nhosts=10, ini=True)

        contacted = ansible_runner.shell(u'awx-manage inventory_import --inventory-name "{0}" --source {1}'.format(inventory.name, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])

        assert inventory.get_related('groups').count == 13
        assert inventory.get_related('hosts').count == 10

    def test_import_license_exceeded(self, api_config_pg, ansible_runner, inventory):
        """Verify import fails if the number of imported hosts exceeds licensed host allowance."""
        api_config_pg.install_license(1000)
        dest = upload_inventory(ansible_runner, nhosts=2000)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected awx-manage inventory_import success." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
        "Number of licensed instances exceeded" in result['stderr']

        assert inventory.get_related('groups').count == 0
        assert inventory.get_related('hosts').count == 0

    def test_import_instance_id_constraint(self, ansible_runner, inventory):
        """Verify that successive inventory imports containing a host with the same name
        and different instance IDs succeed.
        """
        # copy first inventory file to system
        inv_filename = '/tmp/inventory{}.sh'.format(fauxfactory.gen_alphanumeric())
        contacted = ansible_runner.copy(dest=inv_filename, mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(get_ec2_inventory(), indent=4)))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: {0}".format(result)

        # import first inventory file
        contacted = ansible_runner.command("awx-manage inventory_import --inventory-id {0.id} --instance-id-var ec2_id \
            --source {1}".format(inventory, inv_filename))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed." \
                "\n[stdout]\n%s\n[stderr]\n%s".format(result['stdout'], result['stderr'])

        # copy second inventory file to system
        contacted = ansible_runner.copy(dest=inv_filename, mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(get_ec2_inventory(), indent=4)))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: {0}".format(result)

        # import second inventory file
        contacted = ansible_runner.command("awx-manage inventory_import --inventory-id {0.id} --instance-id-var ec2_id \
            --source {1}".format(inventory, inv_filename))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed." \
                "\n[stdout]\n%s\n[stderr]\n%s".format(result['stdout'], result['stderr'])

    @pytest.fixture(scope="function")
    def json_inventory_ipv6(self):
        inventory = {"_meta": {"hostvars": {}}, "ipv6 hosts": []}
        for _ in range(10):
            inventory['ipv6 hosts'].append(utils.random_ipv6())
        return inventory

    def test_import_with_ipv6_hosts(self, ansible_runner, inventory, json_inventory_ipv6):
        """Verify ipv6 inventory import."""
        inv_filename = '/tmp/inventory{}.sh'.format(fauxfactory.gen_alphanumeric())
        contacted = ansible_runner.copy(dest=inv_filename, mode='0755', content="""#!/bin/bash
cat <<EOF
%s
EOF""" % (json.dumps(json_inventory_ipv6, indent=4)))
        for result in contacted.values():
            assert not result.get('failed'), "Failed to create inventory file: {0}.".format(result)

        contacted = ansible_runner.command('awx-manage inventory_import --inventory-id {0.id} --source {1}'.format(inventory, inv_filename))
        for result in contacted.values():
            assert result['rc'] == 0, "awx-manage inventory_import failed:" \
                "\n[stdout]\n%s\n[stderr]\n%s".format(result['stdout'], result['stderr'])
