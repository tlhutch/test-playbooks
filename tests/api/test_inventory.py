import json

import towerkit.tower.inventory
import towerkit.exceptions
import towerkit.utils
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
class Test_Inventory(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_inventory_names(self, factories):
        """Test that we can have inventories with the same name in different organizations."""
        org1 = factories.organization()
        org2 = factories.organization()

        factories.inventory(name="test-org", organization=org1)
        factories.inventory(name="test-org", organization=org2)

    def test_host_update(self, factories):
        """Smart inventory hosts should reflect host changes."""
        host = factories.host()
        inventory = factories.v2_inventory(kind='smart', host_filter="name={0}".format(host.name))
        hosts = inventory.related.hosts.get()

        host.description = fauxfactory.gen_utf8()
        assert hosts.get().results.pop().description == host.description

        host.delete()
        assert hosts.get().count == 0

    def test_host_without_group(self, host_without_group, tower_version_cmp):
        """Verify that /inventory/N/script includes hosts that are not a member of
        any group.
            1) Create inventory with hosts, but no groups
            2) Verify the hosts appear in related->hosts
            2) Verify the hosts appear in related->script
        """
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

    def test_conflict_exception_with_running_update(self, custom_inventory_source):
        """Verify that deleting an inventory with a running update will
        raise a 409 exception
        """
        inventory_pg = custom_inventory_source.get_related("inventory")
        custom_inventory_source.get_related("update").post()
        update_pg = custom_inventory_source.get().get_related("current_update")

        # delete the job_template
        exc_info = pytest.raises(towerkit.exceptions.Conflict, inventory_pg.delete)
        result = exc_info.value[1]
        assert result == {'conflict': 'Resource is being used by running jobs', 'active_jobs': [{'type': '%s' % update_pg.type, 'id': update_pg.id}]}

    def test_update_cascade_delete(self, custom_inventory_source, api_inventory_updates_pg):
        """Verify that associated inventory updates get cascade deleted with custom group
        deletion.
        """
        inv_source_id = custom_inventory_source.id
        custom_inventory_source.update().wait_until_completed()

        # assert that we have an inventory update
        assert api_inventory_updates_pg.get(inventory_source=inv_source_id).count == 1, \
            "Unexpected number of inventory updates. Expected one update."

        # delete custom group and assert that inventory updates deleted
        custom_inventory_source.get_related('group').delete()
        assert api_inventory_updates_pg.get(inventory_source=inv_source_id).count == 0, \
            "Unexpected number of inventory updates after deleting custom group. Expected zero updates."

    def test_child_cascade_delete(self, inventory, host_local, host_without_group, group, api_groups_pg, api_hosts_pg):
        """Verify DELETE removes associated groups and hosts"""
        # Verify inventory group/host counts
        assert inventory.get_related('groups').count == 1
        assert inventory.get_related('hosts').count == 2

        # Delete the inventory
        inventory.delete()

        # Related resources should be forbidden
        with pytest.raises(towerkit.exceptions.NotFound):
            inventory.get_related('groups')

        # Using main endpoint, find any matching groups
        groups_pg = api_groups_pg.get(inventory=inventory.id)

        # Assert no matching groups found
        assert groups_pg.count == 0, "ERROR: not All inventory groups were deleted"

        # Related resources should be forbidden
        with pytest.raises(towerkit.exceptions.NotFound):
            inventory.get_related('hosts')

        # Using main endpoint, find any matching hosts
        hosts_pg = api_hosts_pg.get(inventory=inventory.id)

        # Assert no matching hosts found
        assert hosts_pg.count == 0, "ERROR: not all inventory hosts were deleted"


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Update(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ha_tower
    def test_v1_update_inventory_source(self, cloud_group):
        """Verify successful inventory import using /api/v1/inventory_sources/N/update/."""
        inv_source = cloud_group.get_related('inventory_source')
        assert not inv_source.is_successful

        update = inv_source.get_related('update')
        assert update.can_update

        inv_update = inv_source.update().wait_until_completed()
        assert inv_update.is_successful
        assert inv_source.get().is_successful

    def test_v2_update_inventory_source(self, cloud_inventory):
        """Verify successful inventory import using /api/v2/inventory_sources/N/update/."""
        inv_source = cloud_inventory.related.inventory_sources.get().results.pop()
        assert not inv_source.is_successful

        update = inv_source.get_related('update')
        assert update.can_update

        inv_update = inv_source.update().wait_until_completed()
        assert inv_update.is_successful
        assert inv_source.get().is_successful

    def test_v2_update_all_inventory_sources(self, request, factories):
        """Verify successful inventory imports using /api/v2/inventories/N/update_inventory_sources/."""
        inventory = factories.v2_inventory()
        gce_cred, vmware_cred = [request.getfixturevalue(fixture) for fixture in ('gce_credential', 'vmware_credential')]
        gce_source = factories.v2_inventory_source(inventory=inventory, source='gce', credential=gce_cred)
        vmware_source = factories.v2_inventory_source(inventory=inventory, source='vmware', credential=vmware_cred)

        response = inventory.update_inventory_sources()
        gce_source.wait_until_completed(), vmware_source.wait_until_completed()
        gce_update, vmware_update = [source.related.last_update.get() for source in (gce_source, vmware_source)]

        assert len([entry for entry in response if entry['inventory_source'] == gce_source.id and
                    entry['inventory_update'] == gce_update.id]) == 1
        assert len([entry for entry in response if entry['inventory_source'] == gce_source.id and
                    entry['inventory_update'] == gce_update.id]) == 1
        assert len(response.json) == 2

        assert gce_update.is_successful
        assert gce_source.is_successful
        assert vmware_update.is_successful
        assert vmware_source.is_successful

    @pytest.mark.ha_tower
    def test_inventory_update_with_source_region(self, region_choices, cloud_group_supporting_source_regions):
        """Assess inventory imports with all possible choices for source_regions.

        Note: we expect inventory imports with certain regions to fail. For more context,
        please see https://github.com/ansible/ansible-tower/issues/545.
        """
        # provide list of values for source_regions given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_regions = region_choices['ec2']
        elif cloud_provider == 'azure_rm':
            source_regions = region_choices['azure']
        elif cloud_provider == 'gce':
            source_regions = region_choices['gce']
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)
        unsupported_source_regions = ['cn-north-1', 'us-gov-west-1', 'LON']

        for source_region in source_regions:
            # patch inv_source_pg and launch update
            inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')
            inv_source_pg.patch(source_regions=source_region)
            assert inv_source_pg.source_regions.lower() == source_region.lower(), \
                "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region
            update_pg = inv_source_pg.update().wait_until_completed()

            # assert that the update was successful if used with supported source region
            if source_region not in unsupported_source_regions:
                assert update_pg.is_successful, "inventory_update %s failed with supported region %s." % (update_pg, source_region)
                assert inv_source_pg.get().is_successful, "An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

            # assert that update fails if used with unsupported source region
            else:
                assert update_pg.status == "failed", \
                    "inventory_update %s did not fail with unsupported region %s." % (update_pg, source_region)
                assert inv_source_pg.get().status == "failed", \
                    "An inventory_update failed, but the inventory_source did not fail - %s" % inv_source_pg

            # TODO: Assert specific cloud instance is now listed in group

    def test_inventory_update_with_populated_source_region(self, cloud_group_supporting_source_regions):
        """Tests that hosts are imported when applying source regions containing hosts.

        NOTE: test may fail if our expected test hosts are down.
        """
        # TODO: Once we populate all regions with an instance, don't think we'll need a test
        # tailored to a subset of regions with instances.

        # provide test source_region given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_region = "us-east-1"
        elif cloud_provider == 'azure_rm':
            source_region = "East_US_1"
        elif cloud_provider == 'gce':
            source_region = "us-central1-f"
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)

        # patch inv_source_pg
        inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')
        inv_source_pg.patch(source_regions=source_region)
        assert inv_source_pg.source_regions.lower() == source_region.lower(), \
            "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region

        # assert that the update was successful
        update_pg = inv_source_pg.update().wait_until_completed()
        assert update_pg.is_successful, "inventory_update %s failed with region %s." % (update_pg, source_region)
        assert inv_source_pg.get().is_successful, "An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert that hosts were imported
        assert cloud_group_supporting_source_regions.get().total_hosts > 0, \
            "Unexpected number of hosts returned %s." % cloud_group_supporting_source_regions.total_hosts

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/625')
    @pytest.mark.ansible_integration
    def test_inventory_update_with_unpopulated_source_region(self, cloud_group_supporting_source_regions):
        """Tests that hosts are not imported when applying source regions not containing hosts.

        NOTE: test may fail if someone spins up an instance in one of these regions. Regions correspond as follow:
        * sa-east-1    => South America (Sao Paulo)
        * HKG          => Hong Kong
        * West_Japan   => Japan West
        * asia-east1-c => Asia East (C)
        """
        # TODO: Once we populate all regions with an instance, don't think we'll need a test
        # geared towards empty regions.

        # provide test source_region given each provider
        cloud_provider = cloud_group_supporting_source_regions.get_related('inventory_source').get_related('credential').kind
        if cloud_provider == 'aws':
            source_region = "sa-east-1"
        elif cloud_provider == 'azure':
            source_region = "West_Japan"
        elif cloud_provider == 'gce':
            source_region = "asia-east1-c"
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)

        # patch inv_source_pg
        inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')
        inv_source_pg.patch(source_regions=source_region)
        assert inv_source_pg.source_regions.lower() == source_region.lower(), \
            "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region

        # assert that the update was successful
        update_pg = inv_source_pg.update().wait_until_completed()
        assert update_pg.is_successful, "inventory_update %s failed with region %s." % (update_pg, source_region)
        assert inv_source_pg.get().is_successful, "An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert that no hosts were imported
        assert cloud_group_supporting_source_regions.get().total_hosts == 0, \
            "Unexpected number of hosts returned (%s != 0)." % cloud_group_supporting_source_regions.total_hosts

    @pytest.mark.github("https://github.com/ansible/tower-qa/issues/1247", raises=AssertionError)
    @pytest.mark.parametrize("instance_filter", ["tag-key=Name", "key-name=jenkins", "tag:Name=*"])
    @pytest.mark.ansible_integration
    def test_inventory_update_with_matched_aws_instance_filter(self, aws_group, instance_filter):
        """Tests inventory imports with matched AWS instance filters

        NOTE: test may fail if our expected test hosts are down.
        """
        # patch the inv_source_pg and launch the update
        inv_source_pg = aws_group.get_related('inventory_source')
        inv_source_pg.patch(instance_filters=instance_filter)
        update_pg = inv_source_pg.update().wait_until_completed()

        # assert that the update was successful
        assert update_pg.is_successful, "inventory_update failed - %s" % update_pg
        assert inv_source_pg.get().is_successful, "An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert whether hosts were imported
        # TODO: Assert specific cloud instance is now listed in group
        # (We can probably create our test instance in such a way that
        #  the instance filters only give the test instance - e.g. creating a unique key/value pair).
        assert aws_group.get().total_hosts > 0, "Unexpected number of hosts returned %s." % aws_group.total_hosts

    @pytest.mark.parametrize("instance_filter", ["tag-key=UNMATCHED", "key-name=UNMATCHED", "tag:Name=UNMATCHED"])
    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_inventory_update_with_unmatched_aws_instance_filter(self, aws_group, instance_filter):
        """Tests inventory imports with unmatched AWS instance filters

        NOTE: test may fail if someone spins up an unexpected instance.
        """
        # patch the inv_source_pg and launch the update
        inv_source_pg = aws_group.get_related('inventory_source')
        inv_source_pg.patch(instance_filters=instance_filter)
        update_pg = inv_source_pg.update().wait_until_completed()

        # assert that the update was successful
        assert update_pg.is_successful, "inventory_update failed - %s" % update_pg
        assert inv_source_pg.get().is_successful, "An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert whether hosts were imported
        assert aws_group.get().total_hosts == 0, "Unexpected number of hosts returned (%s != 0)." % aws_group.total_hosts

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/6482", raises=AssertionError)
    @pytest.mark.ansible_integration
    @pytest.mark.parametrize(
        "only_group_by, expected_group_names",
        [
            ("", ["ec2", "images", "keys", "regions", "security_groups", "tags", "types", "vpcs", "zones"],),
            ("availability_zone", ["ec2", "zones"],),
            ("ami_id", ["ec2", "images"],),
            ("instance_id", ["ec2", "instances"],),
            ("instance_type", ["ec2", "types"],),
            ("key_pair", ["ec2", "keys"],),
            ("region", ["ec2", "regions"],),
            ("security_group", ["ec2", "security_groups"],),
            ("availability_zone,ami_id", ["ec2", "zones", "images"],),
        ], ids=["\"\"", "availability_zone", "ami_id", "instance_id", "instance_type", "key_pair", "region", "security_group", "availability_zone,ami_id"])
    def test_aws_only_group_by(self, aws_group, only_group_by, expected_group_names):
        """Tests that expected groups are created when supplying value for only_group_by."""
        inv_source = aws_group.get_related('inventory_source')
        inv_source.group_by = only_group_by

        update = inv_source.update().wait_until_completed()
        assert update.is_successful
        assert inv_source.get().is_successful

        groups = aws_group.get_related('children')
        actual_group_names = [group.name for group in groups.results]
        assert set(actual_group_names) == set(expected_group_names)

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    def test_aws_replace_dash_in_groups_source_variable(self, job_template, aws_group, host_local):
        """Tests that AWS inventory groups will be registered with underscores instead of hyphens
        when using "replace_dash_in_groups" source variable
        """
        job_template.patch(inventory=aws_group.inventory, limit=host_local.name)
        aws_group.get_related('inventory_source').patch(update_on_launch=True,
                                                        source_vars=json.dumps(dict(replace_dash_in_groups=True)))

        # Launch job and check results
        job_pg = job_template.launch().wait_until_completed(timeout=3 * 60)
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # Assert that the inventory_update is marked as successful
        inv_source_pg = aws_group.get_related('inventory_source')
        assert inv_source_pg.is_successful, ("An inventory_update was launched, but the "
                                             "inventory_source is not successful - %s" % inv_source_pg)

        # Assert that hyphen containing tag groups are registered with underscores
        for group_name in ['tag_Test_Flag_2202', 'tag_Test_Flag_2202_Replace_Dash_In_Groups']:
            inv_groups_pg = inv_source_pg.get_related('groups', name__in=group_name)
            assert inv_groups_pg.count, ('An inventory sync was launched with "replace_dash_in_groups: true", '
                                         'but desired group with sanitized tag "{0}" not found.'.format(group_name))

    @pytest.mark.ansible_integration
    @pytest.mark.ha_tower
    @pytest.mark.parametrize('timeout, status, job_explanation', [
        (0, 'successful', ''),
        (60, 'successful', ''),
        (1, 'failed', 'Job terminated due to timeout'),
    ], ids=['no timeout', 'under timeout', 'over timeout'])
    def test_update_with_timeout(self, custom_inventory_source, timeout, status, job_explanation):
        """Tests inventory updates with timeouts."""
        custom_inventory_source.patch(timeout=timeout)

        # launch inventory update and assess spawned update
        update_pg = custom_inventory_source.update().wait_until_completed()
        assert update_pg.status == status, \
            "Unexpected inventory update status. Expected '{0}' but received '{1}.'".format(status, update_pg.status)
        assert update_pg.job_explanation == job_explanation, \
            "Unexpected update job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, update_pg.job_explanation)
        assert update_pg.timeout == custom_inventory_source.timeout, \
            "Update_pg has a different timeout value ({0}) than its inv_source ({1}).".format(update_pg.timeout, custom_inventory_source.timeout)

    def test_single_failed_update_on_launch(self, request, v1):
        """Confirm that only a single inventory update is launched with job template despite failing."""
        cred = v1.credentials.create('aws', user='shouldfail', password='shouldfail')
        request.addfinalizer(cred.teardown)

        group = v1.groups.create(source='ec2', credential=cred)
        request.addfinalizer(group.teardown)

        group.related.inventory_source.patch(update_on_launch=True)
        assert(group.related.inventory_source.get().update_on_launch)

        inv = group.ds.inventory
        jt = v1.job_templates.create(inventory=inv)
        request.addfinalizer(jt.teardown)

        jt.launch().wait_until_completed()
        inv_source = inv.related.inventory_sources.get().results.pop()
        updates = inv_source.related.inventory_updates.get()
        assert(updates.count == 1)
        assert(updates.results.pop().status == 'failed')


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
