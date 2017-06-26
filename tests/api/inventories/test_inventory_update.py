import json

from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class TestInventoryUpdate(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.ha_tower
    def test_v1_update_inventory_source(self, cloud_group):
        """Verify successful inventory import using /api/v1/inventory_sources/N/update/."""
        inv_source = cloud_group.get_related('inventory_source')
        inv_update = inv_source.update().wait_until_completed()
        assert inv_update.is_successful
        assert inv_source.get().is_successful

    def test_v2_update_inventory_source(self, cloud_inventory):
        """Verify successful inventory import using /api/v2/inventory_sources/N/update/."""
        inv_source = cloud_inventory.related.inventory_sources.get().results.pop()
        inv_update = inv_source.update().wait_until_completed()
        assert inv_update.is_successful
        assert inv_source.get().is_successful

    def test_v2_update_all_inventory_sources_with_functional_sources(self, factories):
        """Verify behavior when inventory has functional inventory sources."""
        inventory = factories.v2_inventory()
        gce_cred, vmware_cred = [factories.v2_credential(kind=kind) for kind in ('gce', 'vmware')]
        gce_source = factories.v2_inventory_source(inventory=inventory, source='gce', credential=gce_cred)
        vmware_source = factories.v2_inventory_source(inventory=inventory, source='vmware', credential=vmware_cred)

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=True, inventory_source=gce_source.id) in prelaunch
        assert dict(can_update=True, inventory_source=vmware_source.id) in prelaunch
        assert len(prelaunch.json) == 2

        postlaunch = inventory.related.update_inventory_sources.post()
        gce_update, vmware_update = [source.wait_until_completed().related.last_update.get()
                                     for source in (gce_source, vmware_source)]
        assert dict(inventory_source=gce_source.id, inventory_update=gce_update.id, status="started") in postlaunch
        assert dict(inventory_source=vmware_source.id, inventory_update=vmware_update.id, status="started") in postlaunch
        assert len(postlaunch.json) == 2

        assert gce_update.is_successful
        assert gce_source.is_successful
        assert vmware_update.is_successful
        assert vmware_source.is_successful

    def test_v2_update_all_inventory_sources_with_semifunctional_sources(self, factories):
        """Verify behavior when inventory has an inventory source that is ready for update
        and one that is not.
        """
        inv_source1 = factories.v2_inventory_source()
        inv_source1.ds.inventory_script.delete()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.v2_inventory_source(inventory=inventory)

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=False, inventory_source=inv_source1.id) in prelaunch
        assert dict(can_update=True, inventory_source=inv_source2.id) in prelaunch
        assert len(prelaunch.json) == 2

        postlaunch = inventory.related.update_inventory_sources.post()
        inv_update = inv_source2.wait_until_completed().related.last_update.get()
        assert dict(inventory_source=inv_source1.id, status="Could not start because `can_update` returned False") in postlaunch
        assert dict(inventory_source=inv_source2.id, status="started", inventory_update=inv_update.id) in postlaunch
        assert len(postlaunch.json) == 2

        assert not inv_source1.last_updated
        assert inv_source2.is_successful
        assert inv_update.is_successful

    def test_v2_update_all_inventory_sources_with_nonfunctional_sources(self, factories):
        """Verify behavior when inventory has nonfunctional inventory sources."""
        inv_source = factories.v2_inventory_source()
        inv_source.ds.inventory_script.delete()
        inventory = inv_source.ds.inventory

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=False, inventory_source=inv_source.id) in prelaunch
        assert len(prelaunch.json) == 1

        postlaunch = inventory.related.update_inventory_sources.post()
        assert dict(inventory_source=inv_source.id, status="Could not start because `can_update` returned False") in postlaunch
        assert len(postlaunch.json) == 1

        assert not inv_source.last_updated

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/6564')
    def test_v2_update_duplicate_inventory_sources(self, factories):
        """Verify updating custom inventory sources under the same inventory with
        the same custom script."""
        inv_source1 = factories.v2_inventory_source()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.v2_inventory_source(inventory=inventory,
                                                    inventory_script=inv_source1.ds.inventory_script)

        inv_updates = inventory.update_inventory_sources(wait=True)

        for update in inv_updates:
            assert update.is_successful
        assert inv_source1.get().is_successful
        assert inv_source2.get().is_successful

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/6523")
    def test_update_with_overwrite(self, factories):
        """Verify inventory update with overwrite.
        * Hosts and groups created within our script-spawned group should get deleted.
        * Hosts and groups created outside of our custom group should persist.
        """
        inv_source = factories.v2_inventory_source(overwrite=True)
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed()
        spawned_group = inv_source.related.groups.get().results.pop()

        # associate group and host with script-spawned group
        included_group = factories.group(inventory=inventory)
        included_host = factories.host(inventory=inventory)
        spawned_group.add_group(included_group)
        for group in [spawned_group, included_group]:
            group.add_host(included_host)

        # create excluded inventory resources
        excluded_group = factories.group(inventory=inventory)
        excluded_host, isolated_host = [factories.host(inventory=inventory) for _ in range(2)]
        excluded_group.add_host(excluded_host)

        inv_source.update().wait_until_completed()
        for resource in [included_group, included_host, excluded_group, excluded_host, isolated_host]:
            with pytest.raises(exc.NotFound):
                resource.get()

    def test_update_with_overwrite_vars(self, factories):
        """Verify group and host variables overwritten when enabled."""
        inv_source = factories.v2_inventory_source(overwrite_vars=True)
        inv_source.update().wait_until_completed()
        custom_group = inv_source.related.groups.get().results.pop()

        custom_group.variables = "{'overwrite_me': true}"
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = "{'overwrite_me': true}"

        inv_source.update().wait_until_completed()

        assert not json.loads(custom_group.get().variables)
        for host in hosts.results:
            assert not json.loads(host.get().variables)

    def test_update_without_overwrite_vars(self, factories):
        """Verify group and host variables persist when disabled."""
        inv_source = factories.v2_inventory_source()
        inv_source.update().wait_until_completed()
        custom_group = inv_source.related.groups.get().results.pop()

        variables = "{'overwrite_me': false}"
        custom_group.variables = variables
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = variables

        inv_source.update().wait_until_completed()

        assert custom_group.get().variables == variables
        for host in hosts.results:
            assert host.get().variables == variables

    @pytest.mark.parametrize('verbosity, stdout_lines',
        [(0, ['stdout capture is missing']),
         (1, ['Loaded 1 groups, 5 hosts', 'Inventory variables unmodified',
              'Inventory import completed']),
         (2, ['Reading Ansible inventory source',
              'Finished loading from source',
              'Loaded 1 groups, 5 hosts',
              'Inventory variables unmodified',
              'Inventory import completed'])], ids=['0-warning', '1-info', '2-debug'])
    def test_update_verbosity(self, factories, verbosity, stdout_lines):
        """Verify inventory source verbosity."""
        inv_source = factories.v2_inventory_source(verbosity=verbosity)
        inv_update = inv_source.update().wait_until_completed()

        assert inv_update.is_successful
        assert inv_update.verbosity == inv_source.verbosity
        for line in stdout_lines:
            assert line in inv_update.result_stdout

    @pytest.mark.ha_tower
    def test_update_with_source_region(self, region_choices, cloud_group_supporting_source_regions):
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

    def test_update_with_populated_source_region(self, cloud_group_supporting_source_regions):
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
    def test_update_with_unpopulated_source_region(self, cloud_group_supporting_source_regions):
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
    def test_update_with_matched_aws_instance_filter(self, aws_group, instance_filter):
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
    def test_update_with_unmatched_aws_instance_filter(self, aws_group, instance_filter):
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
    def test_aws_update_with_only_group_by(self, aws_group, only_group_by, expected_group_names):
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

    def test_single_failed_update_on_launch(self, factories):
        """Confirm that only a single inventory update is launched with job template despite failing."""
        cred = factories.v2_credential(kind='aws', inputs=dict(username="fake", password="fake"))
        inv_source = factories.v2_inventory_source(source='ec2', credential=cred, update_on_launch=True)
        jt = factories.v2_job_template(inventory=inv_source.ds.inventory)

        job = jt.launch().wait_until_completed()
        assert job.is_successful

        updates = inv_source.related.inventory_updates.get()
        assert updates.count == 1
        assert updates.results.pop().status == 'failed'
        assert inv_source.get().status == 'failed'
