import json

from towerkit.config import config
from dateutil.parser import parse
from towerkit.utils import load_json_or_yaml, poll_until
from towerkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestInventoryUpdate(APITest):

    def test_v1_update_inventory_source(self, cloud_group):
        """Verify successful inventory import using /api/v1/inventory_sources/N/update/."""
        inv_source = cloud_group.get_related('inventory_source')
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()

    @pytest.mark.ansible_integration
    def test_v2_update_inventory_source(self, cloud_inventory):
        """Verify successful inventory import using /api/v2/inventory_sources/N/update/."""
        inv_source = cloud_inventory.related.inventory_sources.get().results.pop()
        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()

    def test_v2_update_all_inventory_sources_with_functional_sources(self, factories):
        """Verify behavior when inventory has functional inventory sources."""
        inventory = factories.v2_inventory()
        azure_cred, aws_cred = [factories.v2_credential(kind=kind) for kind in ('azure_rm', 'aws')]
        azure_source = factories.v2_inventory_source(inventory=inventory, source='azure_rm', credential=azure_cred)
        ec2_source = factories.v2_inventory_source(inventory=inventory, source='ec2', credential=aws_cred)
        scm_source = factories.v2_inventory_source(inventory=inventory, source='scm',
                                                   source_path='inventories/inventory.ini')

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=True, inventory_source=azure_source.id) in prelaunch
        assert dict(can_update=True, inventory_source=ec2_source.id) in prelaunch
        assert dict(can_update=True, inventory_source=scm_source.id) in prelaunch
        assert len(prelaunch.json) == 3

        postlaunch = inventory.related.update_inventory_sources.post()
        azure_update, ec2_update, scm_update = [source.wait_until_completed(timeout=240).related.last_update.get()
                                                for source in (azure_source, ec2_source, scm_source)]
        filtered_postlaunch = []
        for launched in postlaunch:
            filtered_postlaunch.append(dict(inventory_source=launched['inventory_source'],
                                            inventory_update=launched['inventory_update'],
                                            status=launched['status']))
        assert dict(inventory_source=azure_source.id, inventory_update=azure_update.id, status="started") in filtered_postlaunch
        assert dict(inventory_source=ec2_source.id, inventory_update=ec2_update.id, status="started") in filtered_postlaunch
        assert dict(inventory_source=scm_source.id, inventory_update=scm_update.id, status="started") in filtered_postlaunch
        assert len(postlaunch.json) == 3

        azure_update.assert_successful()
        ec2_update.assert_successful()
        scm_update.assert_successful()

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
        for launched in postlaunch:
            if launched['inventory_source'] == inv_source1.id:
                assert launched['status'] == "Could not start because `can_update` returned False"
            elif launched['inventory_source'] == inv_source2.id:
                assert launched['status'] == "started"
                assert launched['inventory_update'] == inv_update.id
            else:
                pytest.fail('Found unexpected inventory source update: {}'.format(launched))
        assert len(postlaunch.json) == 2

        assert not inv_source1.last_updated
        inv_update.assert_successful()
        inv_source2.assert_successful()

    def test_v2_update_all_inventory_sources_with_nonfunctional_sources(self, factories):
        """Verify behavior when inventory has nonfunctional inventory sources."""
        inventory = factories.v2_inventory()
        inv_source1, inv_source2 = [factories.v2_inventory_source(inventory=inventory) for _ in range(2)]

        inv_source1.ds.inventory_script.delete()
        inv_source2.ds.inventory_script.delete()

        prelaunch = inventory.related.update_inventory_sources.get()
        assert dict(can_update=False, inventory_source=inv_source1.id) in prelaunch
        assert dict(can_update=False, inventory_source=inv_source2.id) in prelaunch
        assert len(prelaunch.json) == 2

        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert dict(status='Could not start because `can_update` returned False', inventory_source=inv_source1.id) in e.value[1]
        assert dict(status='Could not start because `can_update` returned False', inventory_source=inv_source2.id) in e.value[1]
        assert len(e.value[1]) == 2

        assert not inv_source1.last_updated
        assert not inv_source2.last_updated

    def test_v2_update_duplicate_inventory_sources(self, factories):
        """Verify updating custom inventory sources under the same inventory with
        the same custom script."""
        inv_source1 = factories.v2_inventory_source()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.v2_inventory_source(inventory=inventory,
                                                    inventory_script=inv_source1.ds.inventory_script)

        inv_updates = inventory.update_inventory_sources(wait=True)

        for update in inv_updates:
            update.assert_successful()
        inv_source1.get().assert_successful()
        inv_source2.get().assert_successful()

    def test_v2_update_with_no_inventory_sources(self, factories):
        inventory = factories.v2_inventory()
        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert e.value[1] == {'detail': 'No inventory sources to update.'}

    def test_update_with_overwrite(self, factories):
        """Verify inventory update with overwrite.
        * Hosts and groups created within our script-spawned group should get promoted.
        * Hosts and groups created outside of our custom group should persist.
        """
        inv_source = factories.v2_inventory_source(overwrite=True)
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed()
        spawned_group = inv_source.related.groups.get().results.pop()
        spawned_host_ids = [host.id for host in spawned_group.related.hosts.get().results]

        # associate group and host with script-spawned group
        included_group = factories.group(inventory=inventory)
        included_host = factories.host(inventory=inventory)
        spawned_group.add_group(included_group)
        for group in [spawned_group, included_group]:
            group.add_host(included_host)

        # create additional inventory resources
        excluded_group = factories.group(inventory=inventory)
        excluded_host, isolated_host = [factories.host(inventory=inventory) for _ in range(2)]
        excluded_group.add_host(excluded_host)

        inv_source.update().wait_until_completed().assert_successful()

        # verify our script-spawned group contents
        assert spawned_group.related.children.get().count == 0
        assert spawned_host_ids == [host.id for host in spawned_group.related.hosts.get().results]

        # verify that additional inventory resources persist
        for resource in [included_group, included_host, excluded_group, excluded_host, isolated_host]:
            resource.get()

        # verify associations between additional inventory resources
        included_group_hosts = included_group.related.hosts.get()
        assert included_group_hosts.count == 1
        assert included_host.id == included_group_hosts.results.pop().id
        root_groups = inventory.related.root_groups.get()
        assert included_group.id in [group.id for group in root_groups.results]

        excluded_group_hosts = excluded_group.related.hosts.get()
        assert excluded_group_hosts.count == 1
        assert excluded_host.id == excluded_group_hosts.results.pop().id

    def test_update_without_overwrite(self, factories):
        """Verify inventory update without overwrite.
        * Hosts and groups created within our script-spawned group should persist.
        * Hosts and groups created outside of our custom group should persist.
        """
        inv_source = factories.v2_inventory_source()
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed()
        spawned_group = inv_source.related.groups.get().results.pop()
        spawned_host_ids = [host.id for host in spawned_group.related.hosts.get().results]

        # associate group and host with script-spawned group
        included_group = factories.group(inventory=inventory)
        included_host = factories.host(inventory=inventory)
        spawned_group.add_group(included_group)
        for group in [spawned_group, included_group]:
            group.add_host(included_host)

        # create additional inventory resources
        excluded_group = factories.group(inventory=inventory)
        excluded_host, isolated_host = [factories.host(inventory=inventory) for _ in range(2)]
        excluded_group.add_host(excluded_host)

        inv_source.update().wait_until_completed().assert_successful()

        # verify our script-spawned group contents
        spawned_group_children = spawned_group.related.children.get()
        assert spawned_group_children.count == 1
        assert spawned_group_children.results.pop().id == included_group.id
        assert set(spawned_host_ids) | set([included_host.id]) == set([host.id for host in spawned_group.related.hosts.get().results])

        # verify that additional inventory resources persist
        for resource in [included_group, included_host, excluded_group, excluded_host, isolated_host]:
            resource.get()

        # verify associations between additional inventory resources
        included_group_hosts = included_group.related.hosts.get()
        assert included_group_hosts.count == 1
        assert included_host.id == included_group_hosts.results.pop().id

        excluded_group_hosts = excluded_group.related.hosts.get()
        assert excluded_group_hosts.count == 1
        assert excluded_host.id == excluded_group_hosts.results.pop().id

    def test_update_with_overwrite_vars(self, factories, ansible_version_cmp):
        """Verify manually inserted group and host variables get deleted when
        enabled. Final group and host variables should be those sourced from
        the script. Inventory variables should persist.
        """
        inv_source = factories.v2_inventory_source(overwrite_vars=True)
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed().assert_successful()
        custom_group = inv_source.related.groups.get().results.pop()

        inserted_variables = "{'overwrite_me': true}"
        for resource in [inventory, custom_group]:
            resource.variables = inserted_variables
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = inserted_variables

        inv_source.update().wait_until_completed().assert_successful()

        assert inventory.get().variables == load_json_or_yaml(inserted_variables)
        expected_vars = {'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}
        if ansible_version_cmp('2.4.0') < 1:
            # ansible 2.4 doesn't set group variables
            # https://github.com/ansible/ansible/issues/30877
            assert custom_group.get().variables == expected_vars
        for host in hosts.results:
            assert set(host.get().variables[custom_group.name]['hosts']) == set([host.name for host in hosts.results])
            assert host.variables[custom_group.name]['vars'] == expected_vars

    def test_update_without_overwrite_vars(self, factories, ansible_version_cmp):
        """Verify manually inserted group and host variables persist when disabled. Final
        group and host variables should be a union of those sourced from the inventory
        script and those manually inserted. Inventory variables should persist.
        """
        inv_source = factories.v2_inventory_source()
        inventory = inv_source.ds.inventory
        inv_source.update().wait_until_completed().assert_successful()
        custom_group = inv_source.related.groups.get().results.pop()

        inserted_variables = "{'overwrite_me': false}"
        for resource in [inventory, custom_group]:
            resource.variables = inserted_variables
        hosts = custom_group.related.hosts.get()
        for host in hosts.results:
            host.variables = inserted_variables

        inv_source.update().wait_until_completed().assert_successful()

        assert inventory.get().variables == load_json_or_yaml(inserted_variables)
        expected_vars = {'overwrite_me': False, 'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}
        if ansible_version_cmp('2.4.0') < 1:
            # ansible 2.4 doesn't set group variables
            # https://github.com/ansible/ansible/issues/30877
            assert custom_group.get().variables == expected_vars
        for host in hosts.results:
            assert host.get().variables['overwrite_me'] is False
            assert set(host.variables[custom_group.name]['hosts']) == set([host.name for host in hosts.results])
            # update once https://github.com/ansible/ansible/issues/30877 lands
            # assert host.variables[custom_group.name]['vars'] == expected_vars
            assert host.variables[custom_group.name]['vars'] == {'ansible_host': '127.0.0.1', 'ansible_connection': 'local'}

    @pytest.mark.ansible_integration
    def test_update_with_stdout_injection(self, factories, ansible_version_cmp):
        """Verify that we can inject text to update stdout through our script."""
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        inv_script = factories.v2_inventory_script(script=("#!/usr/bin/env python\n"
                                                           "from __future__ import print_function\nimport sys\n"
                                                           "print('TEST', file=sys.stderr)\nprint('{}')"))
        inv_source = factories.v2_inventory_source(inventory_script=inv_script)

        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert "TEST" in inv_update.result_stdout

    def test_update_with_custom_credential(self, factories, ansible_version_cmp):
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        org = factories.organization()
        inv = factories.v2_inventory(organization=org)
        credential_type = factories.credential_type(
            inputs={
                'fields': [{
                    'id': 'password',
                    'type': 'string',
                    'label': 'Password',
                    'secret': True
                }]
            },
            injectors={
                'file': {'template': '[secrets]\npassword={{ password }}'},
                'env': {'AWX_CUSTOM_INI': '{{ tower.filename }}'}
            }
        )
        inv_script = factories.v2_inventory_script(
            organization=org,
            script=("#!/usr/bin/env python\n"
                    "from __future__ import print_function\nimport os, sys\n"
                    "print(open(os.environ['AWX_CUSTOM_INI']).read(), file=sys.stderr)\nprint('{}')")
        )
        inv_source = factories.v2_inventory_source(
            inventory=inv,
            inventory_script=inv_script,
            credential=factories.v2_credential(
                credential_type=credential_type,
                inputs={'password': 'SECRET123'}
            ),
            verbosity=2
        )
        inv_update = inv_source.update().wait_until_completed()
        assert 'password=SECRET123' in inv_update.result_stdout

    @pytest.mark.parametrize('verbosity, stdout_lines',
                             [(0, ['Re-calling script for hostvars individually.']),
                              (1, ['Loaded 1 groups, 5 hosts',
                                   'Inventory import completed']),
                              (2, ['Reading Ansible inventory source',
                                   'Finished loading from source',
                                   'Loaded 1 groups, 5 hosts',
                                   'Inventory variables unmodified',
                                   'Inventory import completed',
                                   'Adding host host_', ' to group group-',
                                   'Adding child group group-', ' to parent all'])],
                             ids=['0-warning', '1-info', '2-debug'])
    def test_update_verbosity(self, is_docker, ansible_version_cmp, factories, verbosity, stdout_lines):
        """Verify inventory source verbosity."""
        if is_docker and verbosity == 0:
            pytest.skip('Dev Container has debug logging so this test will likely fail')

        inv_source = factories.v2_inventory_source(verbosity=verbosity)
        inv_update = inv_source.update().wait_until_completed()

        inv_update.assert_successful()
        assert inv_update.verbosity == inv_source.verbosity
        if verbosity == 0 and ansible_version_cmp('2.4.0') >= 1:
            # https://github.com/ansible/awx/issues/792
            assert inv_update.result_stdout == ''
        else:
            for line in stdout_lines:
                assert line in inv_update.result_stdout

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
                assert update_pg.is_successful, u"inventory_update %s failed with supported region %s." % (update_pg, source_region)
                assert inv_source_pg.get().is_successful, u"An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

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
            source_region = "eastus"
        elif cloud_provider == 'gce':
            source_region = "all"
        else:
            raise NotImplementedError("Unexpected cloud_provider: %s." % cloud_provider)

        # patch inv_source_pg
        inv_source_pg = cloud_group_supporting_source_regions.get_related('inventory_source')
        inv_source_pg.patch(source_regions=source_region)
        assert inv_source_pg.source_regions.lower() == source_region.lower(), \
            "Unexpected value for inv_source_pg.source_regions after patching the inv_source_pg with %s." % source_region

        # assert that the update was successful
        update_pg = inv_source_pg.update().wait_until_completed()
        assert update_pg.is_successful, u"inventory_update %s failed with region %s." % (update_pg, source_region)
        assert inv_source_pg.get().is_successful, u"An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert that hosts were imported
        assert cloud_group_supporting_source_regions.ds.inventory.get().total_hosts > 0, \
            "Unexpected number of hosts returned %s." % cloud_group_supporting_source_regions.total_hosts

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
        elif cloud_provider == 'azure_rm':
            source_region = "japanwest"
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
        assert update_pg.is_successful, u"inventory_update %s failed with region %s." % (update_pg, source_region)
        assert inv_source_pg.get().is_successful, u"An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert that no hosts were imported
        assert cloud_group_supporting_source_regions.ds.inventory.get().total_hosts == 0, \
            "Unexpected number of hosts returned (%s != 0)." % cloud_group_supporting_source_regions.total_hosts

    @pytest.mark.parametrize("instance_filter", ["tag-key=Name", "key-name=jenkins", "tag:Name=*"])
    @pytest.mark.ansible_integration
    def test_update_with_matched_aws_instance_filter(self, factories, instance_filter):
        """Tests inventory imports with matched AWS instance filters. NOTE: test may fail
        if our expected test hosts are down.
        """
        aws_inventory_source = factories.v2_inventory_source(kind='ec2', instance_filters=instance_filter)
        update = aws_inventory_source.update().wait_until_completed()
        update.assert_successful()
        aws_inventory_source.get().assert_successful()

        assert aws_inventory_source.ds.inventory.related.hosts.get().count > 0

    @pytest.mark.parametrize("instance_filter", ["tag-key=UNMATCHED", "key-name=UNMATCHED", "tag:Name=UNMATCHED"])
    @pytest.mark.ansible_integration
    def test_update_with_unmatched_aws_instance_filter(self, aws_group, instance_filter):
        """Tests inventory imports with unmatched AWS instance filters

        NOTE: test may fail if someone spins up an unexpected instance.
        """
        # patch the inv_source_pg and launch the update
        inv_source_pg = aws_group.get_related('inventory_source')
        inv_source_pg.patch(instance_filters=instance_filter)
        update_pg = inv_source_pg.update().wait_until_completed()

        # assert that the update was successful
        assert update_pg.is_successful, u"inventory_update failed - %s" % update_pg
        assert inv_source_pg.get().is_successful, u"An inventory_update was succesful, but the inventory_source is not successful - %s" % inv_source_pg

        # assert whether hosts were imported
        assert aws_group.get().total_hosts == 0, "Unexpected number of hosts returned (%s != 0)." % aws_group.total_hosts

    @pytest.mark.ansible_integration
    @pytest.mark.parametrize("only_group_by, expected_group_names",
                             [("", ["accounts", "ec2", "images", "instance_states", "keys", "platforms", "regions",
                                    "security_groups", "tags", "types", "vpcs", "zones"],),
                              ("availability_zone", ["ec2", "zones"],),
                              ("ami_id", ["ec2", "images"],),
                              ("instance_id", ["ec2", "instances"],),
                              ("instance_type", ["ec2", "types"],),
                              ("key_pair", ["ec2", "keys"],),
                              ("region", ["ec2", "regions"],),
                              ("security_group", ["ec2", "security_groups"],),
                              ("availability_zone,ami_id", ["ec2", "zones", "images"],),
                              ("platform", ["ec2", "platforms"],)],
                             ids=['""', "availability_zone", "ami_id", "instance_id", "instance_type", "key_pair",
                                  "region", "security_group", "availability_zone,ami_id", "platform"])
    def test_aws_update_with_only_group_by(self, aws_group, only_group_by, expected_group_names):
        """Tests that expected groups are created when supplying value for only_group_by."""
        inv_source = aws_group.get_related('inventory_source')
        inv_source.group_by = only_group_by

        update = inv_source.update().wait_until_completed()
        update.assert_successful()
        inv_source.get().assert_successful()

        groups = aws_group.ds.inventory.related.root_groups.get()
        actual_group_names = [group.name for group in groups.results if group.name != aws_group.name]
        assert set(actual_group_names) == set(expected_group_names)

        # confirm desired auth env vars are in update context
        assert 'AWS_ACCESS_KEY_ID' in update.job_env
        assert 'AWS_SECRET_ACCESS_KEY' in update.job_env

    @pytest.mark.ansible_integration
    def test_aws_replace_dash_in_groups_source_variable(self, job_template, aws_group, host_local):
        """Tests that AWS inventory groups will be registered with underscores instead of hyphens
        when using "replace_dash_in_groups" source variable
        """
        job_template.patch(inventory=aws_group.inventory, limit=host_local.name)
        aws_group.get_related('inventory_source').patch(update_on_launch=True,
                                                        source_vars=json.dumps(dict(replace_dash_in_groups=True)))

        # Launch job and check results
        job_pg = job_template.launch().wait_until_completed(timeout=3 * 60)
        assert job_pg.is_successful, u"Job unsuccessful - %s" % job_pg

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

    @pytest.mark.parametrize('inventory_source', ['azure_rm', None], ids=['azure', 'custom'])
    def test_environment_variables_sourced_with_inventory_update_with_azure_credential(self, factories, inventory_source):
        azure_cred = factories.v2_credential(kind='azure_rm', client='SomeClient', cloud_environment='SomeCloudEnvironment',
                                             password='SomePassword', secret='SomeSecret', subscription='SomeSubscription',
                                             tenant='SomeTenant', username='SomeUsername')
        if inventory_source:
            azure = factories.v2_inventory_source(credential=azure_cred, inventory_source=inventory_source)
        else:
            # custom inventory script created when no inventory_source specified
            azure = factories.v2_inventory_source(credential=azure_cred)
        update = azure.update().wait_until_completed()
        job_env = update.job_env
        assert job_env.AZURE_CLIENT_ID == 'SomeClient'
        assert job_env.AZURE_CLOUD_ENVIRONMENT == 'SomeCloudEnvironment'
        assert job_env.AZURE_SECRET == '**********'
        assert job_env.AZURE_SUBSCRIPTION_ID == 'SomeSubscription'
        assert job_env.AZURE_TENANT == 'SomeTenant'

    @pytest.mark.parametrize('source, cred_type', {
        'cloudforms': 'Red Hat CloudForms',
        'rhv': 'Red Hat Virtualization',
        'satellite6': 'Red Hat Satellite 6',
        'vmware': 'VMware vCenter',
    }.items())
    def test_config_parser_properly_escapes_special_characters_in_passwords(self, v2, factories, source, cred_type):
        cred_type = v2.credential_types.get(managed_by_tower=True, name=cred_type).results.pop()
        cred = factories.v2_credential(
            credential_type=cred_type,
            inputs={'host': 'http://example.org', 'username': 'xyz', 'password': 'pass%word'}
        )
        source = factories.v2_inventory_source(source=source, credential=cred)
        inv_update = source.update().wait_until_completed()
        assert 'ERROR! No inventory was parsed, please check your configuration and options' in inv_update.result_stdout
        assert 'SyntaxError' not in inv_update.result_stdout

    @pytest.mark.skip_openshift  # Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_inventory_events_are_inserted_in_the_background(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        ec2_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_update = ec2_source.update().wait_until_completed()

        # the first few events should be created/inserted *after* the job
        # created date and _before_ the job's finished date; this means that
        # events are being asynchronously inserted into the database _while_
        # the job is in "running" state
        events = inv_update.related.events.get(order='id').results
        assert len(events) > 0, "Problem with fixture, AWS inventory update did not produce any events"
        for event in events[:10]:
            assert parse(event.created) > parse(inv_update.created)
            assert parse(event.created) < parse(inv_update.finished)

    def test_inventory_events_are_searchable(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        ec2_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_update = ec2_source.update().wait_until_completed()
        assert inv_update.related.events.get().count > 0
        assert inv_update.related.events.get(search='Updating inventory').count > 0
        assert inv_update.related.events.get(search='SOME RANDOM STRING THAT IS NOT PRESENT').count == 0

    @pytest.mark.ansible_integration
    def test_inventory_hosts_cannot_be_deleted_during_sync(self, factories):
        aws_cred = factories.v2_credential(kind='aws')
        aws_inventory_source = factories.v2_inventory_source(kind='ec2', credential=aws_cred, verbosity=2)

        inv_update = aws_inventory_source.update().wait_until_completed()
        inv_update.assert_successful()

        inv_update = aws_inventory_source.update()
        poll_until(
            lambda: inv_update.get().status == 'running',
            interval=1,
            timeout=15
        )

        hosts = aws_inventory_source.ds.inventory.related.hosts.get()
        host = hosts.results.pop()
        with pytest.raises(exc.Conflict):
            host.delete()

    def test_tower_inventory_sync_success(self, factories):
        target_host = factories.v2_host()
        target_inventory = target_host.ds.inventory
        tower_cred = factories.v2_credential(
            kind='tower',
            inputs={
                'host': config.base_url,
                'username': config.credentials.users.admin.username,
                'password': config.credentials.users.admin.password,
                'verify_ssl': False
            }
        )
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters=target_inventory.id
        )
        inv_update = tower_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert 'Loaded 0 groups, 1 hosts' in inv_update.result_stdout

        loaded_hosts = tower_source.ds.inventory.related.hosts.get()
        assert loaded_hosts.count == 1
        assert loaded_hosts.results[0].name == target_host.name

    def test_tower_inventory_incorrect_password(self, factories):
        tower_cred = factories.v2_credential(
            kind='tower',
            inputs={
                'host': config.base_url,
                'username': config.credentials.users.admin.username,
                'password': 'INVALID!',
                'verify_ssl': False
            }
        )
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters='123',
        )
        inv_update = tower_source.update().wait_until_completed()
        assert inv_update.status == 'failed'
        assert 'Failed to validate the license' in inv_update.result_stdout

    @pytest.mark.parametrize('hostname, error', [
        ['https://###/', 'Invalid URL'],
        ['example.org', 'Failed to validate the license'],
    ])
    def test_tower_inventory_sync_failure_has_descriptive_error_message(self, factories, hostname, error):
        tower_cred = factories.v2_credential(kind='tower', inputs={
            'host': hostname,
            'username': 'x',
            'password': 'y'
        })
        tower_source = factories.v2_inventory_source(
            source='tower', credential=tower_cred,
            instance_filters='123'
        )
        inv_update = tower_source.update().wait_until_completed()
        assert inv_update.status == 'failed'
        assert error in inv_update.result_stdout
