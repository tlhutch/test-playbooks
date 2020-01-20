from dateutil.parser import parse
from awxkit.utils import load_json_or_yaml, poll_until
from awxkit.config import config
from awxkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestInventoryUpdate(APITest):

    def test_update_all_inventory_sources_with_functional_sources(self, factories):
        """Verify behavior when inventory has functional inventory sources."""
        inventory = factories.inventory()
        azure_cred, aws_cred = [factories.credential(kind=kind) for kind in ('azure_rm', 'aws')]
        azure_source = factories.inventory_source(inventory=inventory, source='azure_rm', credential=azure_cred)
        ec2_source = factories.inventory_source(inventory=inventory, source='ec2', credential=aws_cred)
        scm_source = factories.inventory_source(inventory=inventory, source='scm',
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

    def test_update_all_inventory_sources_with_semifunctional_sources(self, factories):
        """Verify behavior when inventory has an inventory source that is ready for update
        and one that is not.
        """
        inv_source1 = factories.inventory_source()
        inv_source1.ds.inventory_script.delete()
        inventory = inv_source1.ds.inventory
        inv_source2 = factories.inventory_source(inventory=inventory)

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

    def test_update_all_inventory_sources_with_nonfunctional_sources(self, factories):
        """Verify behavior when inventory has nonfunctional inventory sources."""
        inventory = factories.inventory()
        inv_source1, inv_source2 = [factories.inventory_source(inventory=inventory) for _ in range(2)]

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

    def test_update_duplicate_inventory_sources(self, factories):
        """Verify updating custom inventory sources under the same inventory with
        the same custom script."""
        inv_source1 = factories.inventory_source()
        inventory = inv_source1.ds.inventory
        inv_script = inv_source1.ds.inventory_script
        inv_source2 = factories.inventory_source(inventory=inventory,
                                                    source_script=inv_script)
        assert inv_source1.source_script == inv_script.id
        assert inv_source2.source_script == inv_source1.source_script

        inv_updates = inventory.update_inventory_sources(wait=True)

        for update in inv_updates:
            update.assert_successful()
        inv_source1.get().assert_successful()
        inv_source2.get().assert_successful()

    def test_update_with_no_inventory_sources(self, factories):
        inventory = factories.inventory()
        with pytest.raises(exc.BadRequest) as e:
            inventory.update_inventory_sources()
        assert e.value[1] == {'detail': 'No inventory sources to update.'}

    def _contents_same(self, *args):
        """Given list1 and list2 which are both lists of pages of API objects
        this asserts that both lists contain the same objects by name
        """
        assert len(args) > 1
        compare_list = []
        for arg in args:
            if isinstance(arg, (list, tuple)):
                # is a results list
                compare_list.append(set([item.name for item in arg]))
            elif hasattr(arg, 'results'):
                # is a page object
                compare_list.append(set(item.name for item in arg.results))
            else:
                # is a single object
                compare_list.append(set([arg.name]))
        for item in compare_list[1:]:
            assert item == compare_list[0]

    def test_empty_groups_child_of_all_group(self, v2, factories):
        shared_org = factories.organization()
        parent_inv = factories.inventory(organization=shared_org)
        custom_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    "_meta": {
        "hostvars": {
            "old_host": {}
        }
    },
    "ungrouped": {
        "hosts": ["old_host"]
    },
    "ghost": {
        "hosts": [],
        "vars": {
            "foobar": "hello_world"
        }
    },
    "ghost2": {
        "hosts": []
    },
    "all": {
        "children": ["ghost3"]
    }
}))"""
        inv_script = factories.inventory_script(
            script=custom_script,
            organization=shared_org,
        )
        inv_source = factories.inventory_source(
            source_script=inv_script,
            organization=shared_org,
            inventory=parent_inv
        )
        assert inv_source.source_script == inv_script.id
        inv_source.update().wait_until_completed().assert_successful()
        groups = parent_inv.related.groups.get().results
        assert len(groups) == 3
        group_names = [group.name for group in groups]
        assert set(group_names) == set(['ghost', 'ghost2', 'ghost3'])

    def test_update_with_overwrite_deletion(self, factories):
        """Verify inventory update with overwrite will not persist old stuff that it imported.
        * Memberships created within our script-spawned group should removed by a 2nd import.
        * Hosts, groups, and memberships created outside of our custom group should persist.
        """
        inv_script = factories.inventory_script(script="""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'ungrouped': {'hosts': ['will_remove_host']},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch1']},
    'switch2': {'hosts': ['host_switch2']},
    'parent_switch1': {'children': ['switch1']},
    'parent_switch2': {'children': ['switch2']},
    'will_remove_group': {'hosts': ['host_2']},
    'parent_group': {'hosts': ['host_1', 'host_2'], 'children': ['child_group', 'child_group2']}
}))""")
        inv_source = factories.inventory_source(
            overwrite=True,
            source_script=inv_script
        )
        assert inv_source.source_script == inv_script.id

        # update and load objects into in-memory dictionaries
        inv_source.update().wait_until_completed().assert_successful()
        groups = {}
        for group in inv_source.related.groups.get().results:
            groups[group.name] = group
        hosts = {}
        for host in inv_source.related.hosts.get().results:
            hosts[host.name] = host

        # make sure content was imported
        assert 'will_remove_host' in hosts
        assert 'will_remove_group' in groups
        self._contents_same(groups['switch1'].get_related('hosts'), hosts['host_switch1'])
        self._contents_same(groups['switch2'].get_related('hosts'), hosts['host_switch2'])
        self._contents_same(groups['parent_switch1'].get_related('children'), groups['switch1'])
        self._contents_same(groups['parent_switch2'].get_related('children'), groups['switch2'])
        self._contents_same(groups['parent_group'].get_related('hosts'), (hosts['host_1'], hosts['host_2']))
        self._contents_same(groups['parent_group'].get_related('children'), (groups['child_group'], groups['child_group2']))

        # manually add not_child to parent_group
        groups['parent_group'].add_group(groups['not_child'])
        # manually remove child group from parent_group
        groups['parent_group'].remove_group(groups['child_group'])

        # Change script to modify relationships
        # changes made:
        # - host_1 is removed from parent group (but still present in import)
        # - child_group2 is removed from parent group (but still present in import)
        # - switch1 and switch2 trade hosts
        # - child_switch1 and 2 trade child groups
        # - "will remove" host / group are removed
        inv_script.script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch2']},
    'switch2': {'hosts': ['host_switch1']},
    'parent_switch1': {'children': ['switch2']},
    'parent_switch2': {'children': ['switch1']},
    'parent_group': {'hosts': ['host_2'], 'children': ['child_group']}
}))"""

        # update and load objects into in-memory dictionaries, again
        inv_source.update().wait_until_completed().assert_successful()
        groups = {}
        for group in inv_source.related.groups.get().results:
            groups[group.name] = group
        hosts = {}
        for host in inv_source.related.hosts.get().results:
            hosts[host.name] = host

        # verify changes
        assert 'will_remove_host' not in hosts
        assert 'will_remove_group' not in groups
        self._contents_same(groups['switch1'].get_related('hosts'), hosts['host_switch2'])
        self._contents_same(groups['switch2'].get_related('hosts'), hosts['host_switch1'])
        self._contents_same(groups['parent_switch1'].get_related('children'), groups['switch2'])
        self._contents_same(groups['parent_switch2'].get_related('children'), groups['switch1'])
        self._contents_same(groups['parent_group'].get_related('hosts'), hosts['host_2'])  # should have removed host_1
        self._contents_same(groups['parent_group'].get_related('children'), groups['child_group'])

    def test_update_without_overwrite(self, factories):
        """Verify inventory update without overwrite.
        * Hosts and groups created within our script-spawned group should persist.
        * Hosts and groups created outside of our custom group should persist.
        """
        inv_source = factories.inventory_source()
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
        inv_source = factories.inventory_source(overwrite_vars=True)
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
        inv_source = factories.inventory_source()
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

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_update_with_stdout_injection(self, factories, ansible_version_cmp):
        """Verify that we can inject text to update stdout through our script."""
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        inv_script = factories.inventory_script(script=("#!/usr/bin/env python\n"
                                                           "from __future__ import print_function\nimport sys\n"
                                                           "print('TEST', file=sys.stderr)\nprint('{}')"))
        inv_source = factories.inventory_source(source_script=inv_script)
        assert inv_source.source_script == inv_script.id

        inv_update = inv_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert "TEST" in inv_update.result_stdout

    def test_update_with_custom_credential(self, factories, ansible_version_cmp):
        if ansible_version_cmp('2.4.0') >= 1 and ansible_version_cmp('2.5.1') < 1:
            # this doesn't work with ansible-inventory from 2.4 through 2.5.1
            pytest.skip('https://github.com/ansible/ansible/issues/33776')
        org = factories.organization()
        inv = factories.inventory(organization=org)
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
        inv_script = factories.inventory_script(
            organization=org,
            script=("#!/usr/bin/env python\n"
                    "from __future__ import print_function\nimport os, sys\n"
                    "print(open(os.environ['AWX_CUSTOM_INI']).read(), file=sys.stderr)\nprint('{}')")
        )
        inv_source = factories.inventory_source(
            inventory=inv,
            source_script=inv_script,
            credential=factories.credential(
                credential_type=credential_type,
                inputs={'password': 'SECRET123'}
            ),
            verbosity=2
        )
        assert inv_source.source_script == inv_script.id
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

        inv_source = factories.inventory_source(verbosity=verbosity)
        inv_update = inv_source.update().wait_until_completed()

        inv_update.assert_successful()
        assert inv_update.verbosity == inv_source.verbosity
        if verbosity == 0 and ansible_version_cmp('2.4.0') >= 1:
            if (ansible_version_cmp('2.8.0') < 0):
                # https://github.com/ansible/awx/issues/792
                assert inv_update.result_stdout == ''
            else:
                for line in inv_update.result_stdout.split('\n'):
                    if 'ERROR' in line:
                        pass
                    else:
                        assert line == ''
        else:
            for line in stdout_lines:
                assert line in inv_update.result_stdout

    @pytest.mark.parametrize('verbosity', [0, 1])
    def test_inventory_plugin_traceback_surfaced(self, factories, verbosity, ansible_version_cmp):
        if ansible_version_cmp('2.9.0') < 0:
            pytest.skip('Custom user plugins were not fixed until Ansible 2.9')
        inv_src = factories.inventory_source(
            source='scm',
            source_path='inventories/user_plugins/fox.yaml',
            verbosity=verbosity
        )
        iu = inv_src.update().wait_until_completed()
        output = iu.result_stdout
        reduced_output = output.replace('\n', '').replace(' ', '')
        assert 'Gering-ding-ding-ding-dingeringeding' in reduced_output, output
        if verbosity == 0:
            assert 'ancient_mystery' not in reduced_output, output
        else:
            assert 'ancient_mystery' in reduced_output, output

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

    @pytest.mark.parametrize('source, cred_type', {
        'cloudforms': 'Red Hat CloudForms',
        'rhv': 'Red Hat Virtualization',
        'satellite6': 'Red Hat Satellite 6',
        'vmware': 'VMware vCenter',
    }.items())
    def test_config_parser_properly_escapes_special_characters_in_passwords(self, v2, factories, source, cred_type):
        cred_type = v2.credential_types.get(managed_by_tower=True, name=cred_type).results.pop()
        cred = factories.credential(
            credential_type=cred_type,
            inputs={'host': 'http://example.org', 'username': 'xyz', 'password': 'pass%word'}
        )
        source = factories.inventory_source(source=source, credential=cred)
        inv_update = source.update().wait_until_completed()
        assert 'ERROR! No inventory was parsed, please check your configuration and options' in inv_update.result_stdout
        assert 'SyntaxError' not in inv_update.result_stdout

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_inventory_events_are_inserted_in_the_background(self, factories, inventory_script_code_with_sleep):
        sleep_time = 20  # similar to AWS inventory plugin performance
        inventory = factories.inventory()
        inv_source = factories.inventory_source(
            source_script=factories.inventory_script(
                script=inventory_script_code_with_sleep(sleep_time),
                organization=inventory.ds.organization
            ),
            inventory=inventory
        )
        # sanity assertion
        assert inv_source.get_related('source_script').script == inventory_script_code_with_sleep(sleep_time)

        inv_update = inv_source.update().wait_until_completed()

        # the first few events should be created/inserted *after* the job
        # created date and _before_ the job's finished date; this means that
        # events are being asynchronously inserted into the database _while_
        # the job is in "running" state
        events = inv_update.related.events.get(order='id', page_size=200).results
        assert len(events) > 0, "Problem with fixture, AWS inventory update did not produce any events"
        '''
        Check for correctness, events should only be created after the job is created.
        '''
        assert all(parse(event.created) > parse(inv_update.created) for event in events)

        '''
        Ensure there is at least 1 event that is saved before the job finishes.
        Note: This isn't gauranteed, but we are pretty sure we can find at least 1 event.
        '''
        assert any(parse(event.created) < parse(inv_update.finished) for event in events)

        '''
        Check that the events are actually streamed
        Require that span over which events are created is at least 95% of the
        time it spent sleeping (not 100% to avoid unintended system performance flake)
        '''
        min_create = min(parse(event.created) for event in events)
        max_create = max(parse(event.created) for event in events)
        assert (max_create - min_create).total_seconds() > sleep_time * 0.95

    def test_inventory_events_are_searchable(self, factories):
        aws_cred = factories.credential(kind='aws')
        ec2_source = factories.inventory_source(source='ec2', credential=aws_cred)
        inv_update = ec2_source.update().wait_until_completed()
        assert inv_update.related.events.get().count > 0
        assert inv_update.related.events.get(search='Updating inventory').count > 0
        assert inv_update.related.events.get(search='SOME RANDOM STRING THAT IS NOT PRESENT').count == 0

    @pytest.mark.ansible_integration
    def test_inventory_hosts_cannot_be_deleted_during_sync(self, factories):
        aws_cred = factories.credential(kind='aws')
        aws_inventory_source = factories.inventory_source(source='ec2', credential=aws_cred, verbosity=2)
        aws_inventory = aws_inventory_source.related.inventory.get()

        inv_update = aws_inventory_source.update().wait_until_completed()
        inv_update.assert_successful()

        inv_update = aws_inventory_source.update()
        poll_until(
            lambda: inv_update.get().status == 'running',
            interval=1,
            timeout=15
        )

        hosts = aws_inventory.related.hosts.get()
        host = hosts.results.pop()
        with pytest.raises(exc.Conflict):
            host.delete()

    # Ansible changes in 2.9 broke this for a while https://github.com/ansible/ansible/issues/61333
    @pytest.mark.ansible_integration
    def test_tower_inventory_sync_success(self, factories):
        target_host = factories.host()
        target_inventory = target_host.ds.inventory
        tower_cred = factories.credential(
            kind='tower',
            inputs={
                'host': config.base_url,
                'username': config.credentials.users.admin.username,
                'password': config.credentials.users.admin.password,
                'verify_ssl': False
            }
        )
        tower_source = factories.inventory_source(
            source='tower', credential=tower_cred,
            instance_filters=target_inventory.id
        )
        inv_update = tower_source.update().wait_until_completed()
        inv_update.assert_successful()
        assert 'Loaded 0 groups, 1 hosts' in inv_update.result_stdout

        loaded_hosts = tower_source.ds.inventory.related.hosts.get()
        assert loaded_hosts.count == 1
        assert loaded_hosts.results[0].name == target_host.name

    def test_inventory_sync_happens_with_job_running(self, factories):
        """Ensure that an inventory sync can happen while a related job is running."""
        inv_source = factories.inventory_source()

        jt = factories.job_template(
            inventory=inv_source.ds.inventory,
            playbook='sleep.yml',
            extra_vars={'sleep_interval': 180},
        )
        jt.ds.inventory.add_host()
        job = jt.launch().wait_until_status('running')

        inv_source.update().wait_until_completed().assert_successful()
        job.assert_status('running')
        job.cancel().wait_until_completed().assert_status('canceled')
