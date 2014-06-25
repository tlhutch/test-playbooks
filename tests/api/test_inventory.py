import pytest
import json
import logging
import common.tower.inventory
import common.exceptions
from tests.api import Base_Api_Test

# https://gist.github.com/cchurch/171de35cb1f01547c813

@pytest.fixture(scope="function")
def import_inventory(request, authtoken, api_inventories_pg, random_organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=random_organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def delete_inventory(request, authtoken, api_inventories_pg, random_organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=random_organization.id,)
    obj = api_inventories_pg.post(payload)
    # NOTE: This intentionally has no finalizer
    return obj

@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory(Base_Api_Test):
    '''
    Verify successful 'awx-manage inventory_import' operation.  This class
    tests import using both --inventory-id and --inventory-name.  Importing
    with, and without, available licenses is also confirmed.
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_import_bad_id(self, ansible_runner, api_inventories_pg, import_inventory):

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

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name "%s" --source /etc/fstab' % common.utils.random_ascii())
        logging.info(result['stdout'])

        # Verify the import failed
        assert result['rc'] == 1, "awx-manage inventory_import succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

    def test_import_by_id(self, ansible_runner, import_inventory):

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' \
            % (import_inventory.id, copy['dest']))
        logging.info(result['stdout']))

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_by_name(self, ansible_runner, import_inventory):

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' \
            % (import_inventory.name, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_ini(self, ansible_runner, import_inventory):

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10, ini=True)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' \
            % (import_inventory.name, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 10

    def test_import_multiple(self, ansible_runner, import_inventory):
        '''Verify that subsequent imports are faster'''
        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=100, ini=True)

        # Run first awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' \
            % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count > 0
        assert import_inventory.get_related('hosts').count == 100

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        first_import = float(seconds) + 60*float(minutes) + 60*60*float(hours)

        # Run second awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s --overwrite' \
            % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        second_import = float(seconds) + 60*float(minutes) + 60*60*float(hours)

        # Run third awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' \
            % (import_inventory.name, copy['dest']))
        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Calculate total seconds. The expected delta format is - H:MM:SS.SSSSS
        (hours, minutes, seconds) = result['delta'].split(':')
        third_import = float(seconds) + 60*float(minutes) + 60*60*float(hours)

        assert first_import > second_import > third_import, \
            "Unexpected timing when importing inventory multiple times: %s, %s, %s" % \
            (first_import, second_import, third_import)

    def test_import_license_exceeded(self, ansible_runner, import_inventory):
        '''Verify awx-manage inventory_import fails if the number of imported hosts will exceed licensed amount'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=2000)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' \
            % (import_inventory.id, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import failed
        assert result['rc'] == 1, "awx-manage inventory_import succeeded unexpectedly:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert import_inventory.get_related('groups').count == 0
        assert import_inventory.get_related('hosts').count == 0

    def test_cascade_delete(self, ansible_runner, delete_inventory, api_groups_pg, api_hosts_pg):
        '''Verify DELETE removes associated groups and hosts'''

        # Upload inventory script
        copy = common.tower.inventory.upload_inventory(ansible_runner, nhosts=10)

        # Run awx-manage inventory_import
        result = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' \
            % (delete_inventory.id, copy['dest']))
        logging.info(result['stdout'])

        # Verify the import completed successfully
        assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
            % (result['stdout'], result['stderr'])

        # Verify inventory group/host counts
        assert delete_inventory.get_related('groups').count > 0
        assert delete_inventory.get_related('hosts').count == 10

        # Delete the inventory
        delete_inventory.delete()

        # Related resources should be forbidden
        with pytest.raises(common.exceptions.Forbidden_Exception):
            delete_inventory.get_related('groups')
        # Assert associated groups have been deleted
        groups_pg = api_groups_pg.get(id=delete_inventory.id)
        assert groups_pg.count == 0, "ERROR: not All inventory groups were deleted"

        # Related resources should be forbidden
        with pytest.raises(common.exceptions.Forbidden_Exception):
            delete_inventory.get_related('hosts')
        # Assert associated hosts have been deleted
        hosts_pg = api_hosts_pg.get(id=delete_inventory.id)
        assert hosts_pg.count == 0, "ERROR: not all inventory hosts were deleted"
