from awxkit import utils
import awxkit.exceptions as exc
import pytest

import fauxfactory

from tests.api import APITest


def hostnames_from_group_prefixes(prefixes, start=1, finish=5):
    ids = ['0{}'.format(i) if len(str(i)) == 1 else str(i) for i in range(start, finish + 1)]
    host_suffixes = ['host_{}'.format(i) for i in ids]
    hostnames = set()
    for prefix in prefixes:
        for host in host_suffixes:
            hostnames.add('{0}_{1}'.format(prefix, host))
    return hostnames


@pytest.mark.usefixtures('authtoken')
class TestSCMInventorySource(APITest):

    inventory_hostnames = hostnames_from_group_prefixes(['ungrouped', 'group_one', 'group_one_and_two',
                                                         'group_one_two_and_three', 'group_two',
                                                         'group_two_and_three', 'group_three'])

    more_inventory_hostnames = hostnames_from_group_prefixes(['ungrouped'], start=6, finish=10)
    more_inventory_hostnames.update(hostnames_from_group_prefixes(['group_four', 'group_four_and_five',
                                                                   'group_four_five_and_six', 'group_five',
                                                                   'group_five_and_six', 'group_six']))

    even_more_inventory_hostnames = hostnames_from_group_prefixes(['ungrouped'], start=11, finish=15)
    even_more_inventory_hostnames.update(hostnames_from_group_prefixes(['group_seven', 'group_seven_and_eight',
                                                                        'group_seven_eight_and_nine', 'group_eight',
                                                                        'group_eight_and_nine', 'group_nine']))

    all_inventory_hostnames = inventory_hostnames | more_inventory_hostnames | even_more_inventory_hostnames

    def wait_until_job_events_stable(self, job):
        event_count = job.related.job_events.get().count
        for _ in range(10):
            utils.logged_sleep(2)
            this_count = job.related.job_events.get().count
            if this_count == event_count:
                return True
            event_count = this_count

    @pytest.mark.ansible_integration
    def test_project_lists_desired_inventory_files(self, factories):
        project = factories.project()
        inventory_files = project.related.inventory_files.get()

        for desired_file in ('inventories/inventory.ini', 'inventories/more_inventories/inventory.ini',
                             'inventories/more_inventories/even_more_inventories/inventory.ini'):
            assert desired_file in inventory_files

        for listed_file in inventory_files:
            assert 'host_vars/' not in listed_file
            assert 'group_vars/' not in listed_file

    @pytest.fixture(scope='class', params=['inventories/inventory.ini', 'inventories/dyn_inventory.py',
                                           'inventories/metaless_dyn_inventory.py'])
    def scm_inv_source_with_group_and_host_var_dirs(self, request, class_factories):
        inv_source = class_factories.inventory_source(source='scm', source_path=request.param)
        inv_source.update().wait_until_completed().assert_successful()
        scm_inv_sources = inv_source.ds.project.related.scm_inventory_sources.get().results
        assert len(scm_inv_sources) == 1
        assert scm_inv_sources[0].id == inv_source.id
        return inv_source.get()

    @pytest.fixture(scope='class')
    def uses_group_vars(self, ansible_version_cmp):
        return ansible_version_cmp('2.5.0') >= 0

    complex_var = [{"dir": "/opt/gwaf/logs", "sourcetype": "gwaf", "something_else": [1, 2, 3]}]

    @pytest.mark.parametrize('kind, plugin_file, introduced_in', [
        ('azure_rm', 'inventories/azure_rm.yml', '2.7'),
        ('aws', 'inventories/aws_ec2.yml', '2.5'),
        ('openstack', 'inventories/openstack.yml', '2.7'), # https://github.com/ansible/awx/issues/3547
        # ('gce', 'inventories/gcp_compute.yml') # blocked by https://github.com/ansible/ansible/issues/54406
        # what the minimum gcp_compute.yml is may still be up for debate, may need to update it.
        # For example, you must specify project in config file as well as on cred because that is what you always have to do
        # e.g. double specification is required and while not ideal, it is a seperate problem.
    ])
    def test_plugin_configs_as_scm_inventory_sources(self, factories, kind, plugin_file, introduced_in, ansible_version_cmp):
        if ansible_version_cmp(introduced_in) < 0:
            pytest.skip("Inventory plugin was not yet introduced in version of Ansible being ran.")
        cred = factories.credential(kind=kind)
        project = factories.project()
        inv_src = factories.inventory_source(source='scm', source_path=plugin_file, credential=cred, project=project)
        inv_src.update().wait_until_completed().assert_successful()
        inv = inv_src.related.inventory.get()
        assert len(inv.related.hosts.get().results) > 0
        # TODO: Come up with minimum hostvars and groups we want to see from these plugins

    @pytest.mark.ansible_integration
    def test_scm_inventory_hosts_and_host_vars(self, scm_inv_source_with_group_and_host_var_dirs):
        inv_source = scm_inv_source_with_group_and_host_var_dirs
        inventory = inv_source.ds.inventory
        for related_hosts in (inventory.related.hosts, inv_source.related.hosts):
            hosts = related_hosts.get(page_size=200).results
            assert set([host.name for host in hosts]) == self.inventory_hostnames

        group_one_host_01 = inventory.related.hosts.get(name='group_one_host_01').results.pop()
        for group_one_host_01_vars in [group_one_host_01.variables, group_one_host_01.related.variable_data.get()]:
            assert group_one_host_01_vars.group_one_host_01_has_this_var
            assert group_one_host_01_vars.group_one_host_01_should_have_this_var
            assert 'group_one_host_01_should_not_have_this_var' not in group_one_host_01_vars

        group_two_host_01 = inventory.related.hosts.get(name='group_two_host_01').results.pop()
        for group_two_host_01_vars in [group_two_host_01.variables, group_two_host_01.related.variable_data.get()]:
            assert group_two_host_01_vars.group_two_host_01_has_this_var

        group_three_host_01 = inventory.related.hosts.get(name='group_three_host_01').results.pop()
        for group_three_host_01_vars in [group_three_host_01.variables,
                                         group_three_host_01.related.variable_data.get()]:
            assert group_three_host_01_vars.group_three_host_01_has_this_var

    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/2301', skip=True)
    @pytest.mark.ansible_integration
    def test_scm_inventory_groups_and_group_vars(self, scm_inv_source_with_group_and_host_var_dirs, uses_group_vars):
        inv_source = scm_inv_source_with_group_and_host_var_dirs
        inventory = inv_source.ds.inventory.get()

        desired_groups = set(['group_one', 'group_two', 'group_three'])
        for related_groups in (inventory.related.groups, inv_source.related.groups):
            groups = inventory.related.groups.get().results
            assert set([group.name for group in groups]) == desired_groups

        group_one = inventory.related.groups.get(name='group_one').results.pop()
        group_one_hosts = group_one.related.hosts.get(page_size=200).results
        desired_hosts = hostnames_from_group_prefixes(['group_one', 'group_one_and_two', 'group_one_two_and_three'])
        assert set([host.name for host in group_one_hosts]) == desired_hosts

        if uses_group_vars:
            group_one_vars = [group_one.variables, group_one.related.variable_data.get()]
        else:
            group_one_vars = []
            for host in group_one_hosts:
                group_one_vars.extend([host.variables, host.related.variable_data.get()])
        for host in group_one_hosts:
            for group_vars in group_one_vars:
                assert group_vars.is_in_group_one
                assert group_vars.group_one_should_have_this_var
                assert group_vars.complex_var == self.complex_var
                assert 'group_one_should_not_have_this_var' not in group_vars

        group_two = inventory.related.groups.get(name='group_two').results.pop()
        group_two_hosts = group_two.related.hosts.get(page_size=200).results
        desired_hosts = hostnames_from_group_prefixes(['group_two', 'group_one_and_two', 'group_two_and_three',
                                                       'group_one_two_and_three'])
        assert set([host.name for host in group_two_hosts]) == desired_hosts

        if uses_group_vars:
            group_two_vars = [group_two.variables, group_two.related.variable_data.get()]
        else:
            group_two_vars = [host.variables, host.related.variable_data.get()]
        for host in group_two_hosts:
            for group_vars in group_two_vars:
                assert group_vars.is_in_group_two

        group_three = inventory.related.groups.get(name='group_three').results.pop()
        group_three_hosts = group_three.related.hosts.get(page_size=200).results
        desired_hosts = hostnames_from_group_prefixes(['group_three', 'group_two_and_three', 'group_one_two_and_three'])
        assert set([host.name for host in group_three_hosts]) == desired_hosts

        if uses_group_vars:
            group_three_vars = [group_three.variables, group_three.related.variable_data.get()]
        else:
            group_three_vars = [host.variables, host.related.variable_data.get()]
        for host in group_three_hosts:
            for group_vars in group_three_vars:
                assert group_vars.is_in_group_three

        if uses_group_vars:
            assert inventory.variables.inventories_var
            assert inventory.related.variable_data.get().inventories_var
        else:
            hosts = inventory.related.hosts.get(page_size=100).results
            for host in hosts:
                assert host.variables.inventories_var
                assert host.related.variable_data.get().inventories_var

    def test_scm_inv_source_with_overwrite(self, factories):
        inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                   overwrite=True)
        inv_source.update().wait_until_completed().assert_successful()

        for related_hosts in (inv_source.ds.inventory.related.hosts, inv_source.related.hosts):
            hosts = related_hosts.get(page_size=200).results
            assert set([host.name for host in hosts]) == self.inventory_hostnames

        inv_source.source_path = 'inventories/more_inventories/dyn_inventory.py'
        inv_source.update().wait_until_completed().assert_successful()

        for related_hosts in (inv_source.ds.inventory.related.hosts, inv_source.related.hosts):
            hosts = related_hosts.get(page_size=200).results
            assert set([host.name for host in hosts]) == self.more_inventory_hostnames

    @pytest.mark.parametrize('source_paths',
                             [('inventories/inventory.ini', 'inventories/more_inventories/inventory.ini',
                               'inventories/more_inventories/even_more_inventories/inventory.ini'),
                              ('inventories/dyn_inventory.py', 'inventories/more_inventories/dyn_inventory.py',
                               'inventories/more_inventories/even_more_inventories/dyn_inventory.py')],
                             ids=('static', 'dynamic'))
    def test_scm_inv_sources_with_shared_project(self, factories, source_paths, uses_group_vars):
        project = factories.project()
        inventory = factories.inventory(organization=project.ds.organization)
        inv_sources = [factories.inventory_source(source='scm', inventory=inventory, project=project,
                                                     source_path=source_path) for source_path in source_paths]
        for inv_source in inv_sources:
            inv_source.update()
        for inv_source in inv_sources:
            inv_source.wait_until_completed().assert_successful()

        hosts = inventory.related.hosts.get(page_size=200).results
        assert set([host.name for host in hosts]) == self.all_inventory_hostnames

        for hostname in ('group_one_host_01', 'group_four_host_01', 'group_seven_host_01'):
            host = [host for host in hosts if host.name == hostname].pop()
            group_name = hostname.split('_host_01')[0]
            host_var_ls = [host.variables, host.related.variable_data.get()]
            if uses_group_vars:
                group = host.related.groups.get(name=group_name).results.pop().get()
                group_var_ls = [group.variables, group.related.variable_data.get()]
            else:
                group_var_ls = host_var_ls

            for host_vars, group_vars in zip(host_var_ls, group_var_ls):
                assert host_vars['{}_should_have_this_var'.format(hostname)]
                assert '{}_should_not_have_this_var'.format(hostname) not in host_vars

                assert group_vars['is_in_{}'.format(group_name)]
                assert group_vars['{}_should_have_this_var'.format(group_name)]
                assert '{}_should_not_have_this_var'.format(group_name) not in group_vars

        desired_groups = set(['group_one', 'group_two', 'group_three', 'group_four', 'group_five', 'group_six',
                              'group_seven', 'group_eight', 'group_nine'])
        groups = inventory.related.groups.get().results
        assert set([g.name for g in groups]) == desired_groups

        hosts = inv_sources[0].related.hosts.get(page_size=200).results
        assert set([h.name for h in hosts]) == self.inventory_hostnames

        hosts = inv_sources[1].related.hosts.get(page_size=200).results
        assert set([h.name for h in hosts]) == self.more_inventory_hostnames

        hosts = inv_sources[2].related.hosts.get(page_size=200).results
        assert set([h.name for h in hosts]) == self.even_more_inventory_hostnames

        for inv_source, desired_groups in zip(inv_sources, [set(['group_one', 'group_two', 'group_three']),
                                                            set(['group_four', 'group_five', 'group_six']),
                                                            set(['group_seven', 'group_eight', 'group_nine'])]):
            groups = inv_source.related.groups.get().results
            assert set([g.name for g in groups]) == desired_groups

    def test_scm_inv_source_multiple_updates_without_update_on_project_update(self, factories):
        scm_inv_source = factories.inventory_source(source='scm')
        for source_path in ('inventories/inventory.ini', 'inventories/dyn_inventory.py'):
            scm_inv_source.source_path = source_path
            for _ in range(2):
                scm_inv_source.update().wait_until_completed().assert_successful()
        assert scm_inv_source.related.inventory_updates.get().count == 4
        assert scm_inv_source.ds.project.related.project_updates.get(launch_type='manual').count == 1

    def test_scm_inv_source_update_sources_custom_credential(self, factories):
        credential_type = factories.credential_type(inputs=dict(fields=[dict(id='test_env', label='TEST_ENV')]),
                                                    injectors=dict(env=dict(TEST_ENV='{{ test_env }}')))
        credential = factories.credential(credential_type=credential_type,
                                             inputs=dict(test_env='TEST_ENV_1'))
        inv_source = factories.inventory_source(source='scm', source_path='inventories/dyn_inventory_test_env.py',
                                                   credential=credential)
        inv_source.update().wait_until_completed().assert_successful()
        host = inv_source.ds.inventory.related.hosts.get(name='localhost').results.pop()
        assert host.variables.test_env == 'TEST_ENV_1'

    @pytest.mark.parametrize('source_path', ['inventories/inventory.ini', 'inventories/dyn_inventory.py'])
    def test_project_launch_using_update_on_project_update_with_scm_change(self, git_file_path, factories, v2,
                                                                           source_change_add_and_remove, source_path):
        """Verifies that an scm inventory sync runs after running a job that commits code to its upstream repo"""
        project = factories.project(scm_url=git_file_path)
        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 0

        inv_source = factories.inventory_source(source='scm', project=project,
                                                   source_path=source_path,
                                                   update_on_project_update=True)
        inv_source.wait_until_completed()
        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 1

        source_change_add_and_remove()

        project.update().wait_until_completed().assert_successful()
        inv_source.wait_until_completed()

        assert project.related.project_updates.get(launch_type='manual').count == 2
        assert project.related.project_updates.get(launch_type='sync').count == 1
        assert inv_source.related.inventory_updates.get().count == 2

    @pytest.mark.parametrize('source_path', ['inventories/inventory.ini', 'inventories/dyn_inventory.py'])
    def test_project_launch_using_update_on_project_update_without_scm_change(self, factories, source_path):
        project = factories.project()
        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 0

        inv_source = factories.inventory_source(source='scm', project=project,
                                                   source_path=source_path,
                                                   update_on_project_update=True)
        inv_source.wait_until_completed().assert_successful()

        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 1
        assert inv_source.related.inventory_updates.get().count == 1

        project.update().wait_until_completed().assert_successful()

        assert project.related.project_updates.get(launch_type='manual').count == 2
        assert project.related.project_updates.get(launch_type='sync').count == 1
        assert inv_source.related.inventory_updates.get().count == 1

    @pytest.mark.yolo
    def test_inventory_update_using_update_on_project_update_without_scm_change(self, factories, v2):
        """Verifies that an scm inventory sync runs even without changes to scm"""
        inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                   update_on_project_update=True)
        inv_source.wait_until_completed()
        project = inv_source.ds.project

        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 1
        assert inv_source.related.inventory_updates.get().count == 1

        inv_source.update().wait_until_completed().assert_successful()

        assert project.related.project_updates.get(launch_type='manual').count == 1
        assert project.related.project_updates.get(launch_type='sync').count == 2
        assert inv_source.related.inventory_updates.get().count == 2

    def test_cancel_shared_parent_project_update_after_source_change(self, factories, git_file_path,
                                                                     source_change_add_and_remove):
        project = factories.project(scm_url=git_file_path)
        inv_sources = [factories.inventory_source(source='scm', project=project,
                                                     source_path='inventories/inventory.ini') for _ in range(3)]
        inv_source_ids = set([source.id for source in inv_sources])
        project_inv_source_ids = set([source.id for source in project.related.scm_inventory_sources.get().results])
        assert inv_source_ids == project_inv_source_ids
        inv_sources[0].update().wait_until_completed()  # populate host ungrouped_host_01

        for inv_source in inv_sources:
            inv_source.update_on_project_update = True

        source_change_add_and_remove()

        update = project.update().wait_until_status('running')
        # wait until update spawns the inventory updates
        utils.poll_until(lambda: update.get_related('scm_inventory_updates').count, interval=0.5, timeout=30)

        assert update.related.cancel.get()['can_cancel']
        update.related.cancel.post()
        # project update will still probably be successful, because this cancel is
        # done after the project_upate.yml playbook is finished, in post_run_hook
        update.wait_until_completed()

        for inv_update in update.get_related('scm_inventory_updates').results:
            inv_update.assert_status('canceled')

        # although the last update may have been successful status, this would
        # still leave the inventory source with a mis-matched version
        update2 = project.update().wait_until_completed()
        assert update2.get_related('scm_inventory_updates').count == 3

        # subsequent updates should not update the inventory sources
        # because they are now up-to-date
        update3 = project.update().wait_until_completed()
        assert update3.get_related('scm_inventory_updates').count == 0

    @pytest.mark.github('https://github.com/ansible/tower-qa/issues/2432', skip=True)
    @pytest.mark.ansible_integration
    def test_custom_credential_affects_ansible_env_of_scm_inventory(self, factories,
                                                                    scm_inv_source_with_group_and_host_var_dirs):
        inv_source = scm_inv_source_with_group_and_host_var_dirs
        inventory = inv_source.ds.inventory
        host = inventory.related.hosts.get(name='ungrouped_host_01').results.pop()

        inputs = dict(fields=[dict(id='env_var', label='ENV_VAR')])
        injectors = dict(env=dict(ENV_VAR='{{ env_var }}'))
        cred_type = factories.credential_type(kind='cloud', inputs=inputs, injectors=injectors)
        env_var = 'THIS_IS_A_TEST_ENV_VAR'
        cred = factories.credential(credential_type=cred_type, inputs=dict(env_var=env_var))

        jt = factories.job_template(inventory=inventory, project=inv_source.ds.project, limit=host.name,
                                       playbook='ansible_env.yml')
        jt.add_credential(cred)
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        event = job.related.job_events.get(host=host.id, task='debug').results.pop()
        ansible_env = event.event_data.res.ansible_env
        assert ansible_env.ENV_VAR == env_var

    def test_scm_inventory_disallows_manual_project(self, skip_if_openshift, factories, project_ansible_playbooks_manual):
        desired_error = {'source_project': ['Cannot use manual project for SCM-based inventory.']}
        with pytest.raises(exc.BadRequest) as e:
            factories.inventory_source(source='scm', project=project_ansible_playbooks_manual)
        assert e.value.msg == desired_error

        inv_source = factories.inventory_source(source='scm')
        with pytest.raises(exc.BadRequest) as e:
            inv_source.source_project = project_ansible_playbooks_manual.id
        assert e.value.msg == desired_error

    def test_scm_inventory_disallows_vault_credentials(self, factories):
        project = factories.project(scm_type='git')
        vault_credential = factories.credential(kind='vault', vault_password='abc123')
        desired_error = 'Credentials of type insights and vault are disallowed for scm inventory sources.'

        with pytest.raises(exc.BadRequest) as e:
            factories.inventory_source(
                source='scm', source_path='inventories/inventory.ini',
                project=project, credential=vault_credential
            )
        assert e.value.msg == {'credential': [desired_error]}

        with pytest.raises(exc.BadRequest) as e:
            iu = factories.inventory_source(
                source='scm', source_path='inventories/inventory.ini',
                project=project
            )
            iu.related.credentials.post({
                'associate': True, 'id': vault_credential.id
            })
        assert e.value.msg == {'msg': desired_error}

    def test_scm_inv_source_is_schedulable_without_update_on_project_update(self, factories):
        scm_inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini')
        scm_inv_source.add_schedule()

        with pytest.raises(exc.BadRequest) as e:
            scm_inv_source.update_on_project_update = True
        assert e.value.msg == {'update_on_project_update': ['Setting not compatible with existing schedules.']}
        assert not scm_inv_source.update_on_project_update

    def test_scm_inv_source_isnt_schedulable_with_update_on_project_update(self, factories):
        scm_inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                       update_on_project_update=True)
        with pytest.raises(exc.BadRequest) as e:
            scm_inv_source.add_schedule()
        assert e.value.msg == {'unified_job_template': ['Inventory sources with `update_on_project_update` cannot'
                                                            ' be scheduled. Schedule its source project `{0.name}` '
                                                            'instead.'.format(scm_inv_source.ds.project)]}

    def test_scm_inv_source_with_update_on_launch_cannot_update_on_project_update(self, v2, factories):
        inventory = factories.inventory()
        project = factories.project(organization=inventory.ds.organization)
        bad_payload = factories.inventory_source.payload(source='scm', source_path='inventories/inventory.ini',
                                                            update_on_launch=True, update_on_project_update=True,
                                                            inventory=inventory, project=project)
        desired_error = {'update_on_launch': ['Cannot update SCM-based inventory source on launch if set to update '
                                              'on project update. Instead, configure the corresponding source project '
                                              'to update on launch.']}
        with pytest.raises(exc.BadRequest) as e:
            v2.inventory_sources.post(bad_payload)
        assert e.value.msg == desired_error

        inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                   update_on_launch=True, inventory=inventory, project=project)
        with pytest.raises(exc.BadRequest) as e:
            inv_source.update_on_project_update = True
        assert e.value.msg == desired_error

        inv_source.update_on_launch = False
        inv_source.update_on_project_update = True

        with pytest.raises(exc.BadRequest) as e:
            inv_source.update_on_launch = True
        assert e.value.msg == desired_error

    @pytest.mark.yolo
    def test_scm_inv_source_with_update_on_launch_is_synced_on_job_launch(self, factories):
        inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                   update_on_launch=True)
        jt = factories.job_template(inventory=inv_source.ds.inventory)

        assert not inv_source.related.inventory_updates.get().results
        job = jt.launch().wait_until_completed()
        job.assert_successful()

        self.wait_until_job_events_stable(job)

        inv_updates = inv_source.related.inventory_updates.get().results
        assert len(inv_updates) == 1
        inv_update = inv_updates[0]
        assert inv_update.launch_type == 'dependency'
        assert inv_update.finished < job.started

        job_host_summaries = job.related.job_host_summaries.get(page_size=200).results
        hostnames = set([summary.summary_fields.host.name for summary in job_host_summaries])
        assert hostnames == self.inventory_hostnames

    def test_scm_inv_source_with_update_on_project_update_synced_within_parent_project_update(self, factories):
        project = factories.project()
        scm_inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                       project=project)
        scm_inv_source.update_on_project_update = True

        parent_update = project.update().wait_until_completed()
        parent_update.assert_successful()
        scm_inv_source.get().assert_successful()

        inv_updates = scm_inv_source.related.inventory_updates.get().results
        assert len(inv_updates) == 1
        inv_update = inv_updates[0]

        assert parent_update.started < inv_update.started
        assert parent_update.finished > inv_update.finished

    def test_scm_inv_source_with_update_on_project_update_sync_doesnt_occur_on_project_update_error(self, factories):
        project = factories.project()
        inv_source = factories.inventory_source(source='scm', project=project,
                                                   source_path='inventories/inventory.ini')
        inv_source.update_on_project_update = True
        project.scm_url = 'notadomain.fail'
        assert project.update().wait_until_completed().status == 'failed'
        assert inv_source.related.inventory_updates.get().count == 0

    def test_project_update_for_scm_inv_source_with_running_update_on_project_update(self, factories):
        project = factories.project()
        scm_inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                       project=project)
        scm_inv_source.update_on_project_update = True

        #  update the project and immediately schedule another update
        parent_update = project.update().wait_until_status('running')
        subsequent_update = project.update()
        scm_inv_source.wait_until_completed().assert_successful()

        inv_updates = scm_inv_source.related.inventory_updates.get().results
        assert len(inv_updates) == 1
        inv_update = inv_updates[0]

        subsequent_update.wait_until_completed()
        parent_update.get()

        assert parent_update.started < inv_update.started
        assert parent_update.finished > inv_update.finished
        assert parent_update.finished < subsequent_update.started

    def test_scm_inv_source_and_project_with_update_on_launch(self, factories):
        project = factories.project(scm_type='git', scm_delete_on_update=True, scm_update_on_launch=True)
        inv_source = factories.inventory_source(
            source='scm', source_path='inventories/inventory.ini',
            update_on_launch=True, overwrite=True,
            project=project
        )
        jt = factories.job_template(inventory=inv_source.ds.inventory, project=project)
        # Job launch triggers update of project-inv-src and project itself
        job = jt.launch().wait_until_completed()
        inv_source.related.inventory_updates.get().results[0].assert_successful()
        # project spawns multiple updates
        for pu in project.related.project_updates.get().results:
            pu.assert_successful()
        job.assert_successful()

    def test_scm_inv_source_update_on_project_update_with_project_update_on_launch(self, factories):
        scm_inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini')
        project = scm_inv_source.ds.project
        jt = factories.job_template(inventory=scm_inv_source.ds.inventory, project=project)

        scm_inv_source.update_on_project_update = True
        project.scm_update_on_launch = True

        assert not scm_inv_source.related.inventory_updates.get().count
        assert project.related.project_updates.get(launch_type='manual').count == 1

        job = jt.launch().wait_until_completed()
        job.assert_successful()

        self.wait_until_job_events_stable(job)

        assert project.related.project_updates.get(launch_type='manual').count == 1
        dep_project_updates = project.related.project_updates.get(launch_type='dependency').results
        assert len(dep_project_updates) == 1
        project_update = dep_project_updates[0]

        scm_updates = scm_inv_source.related.inventory_updates.get().results
        assert len(scm_updates) == 1
        scm_update = scm_updates[0]

        assert project_update.started < scm_update.started
        assert scm_update.finished < project_update.finished

        job_host_summaries = job.related.job_host_summaries.get(page_size=200).results
        hostnames = set([summary.summary_fields.host.name for summary in job_host_summaries])
        assert hostnames == self.inventory_hostnames

    def test_canceled_inventory_update_during_project_update(self, factories):
        project = factories.project()
        inv_source = factories.inventory_source(source='scm', source_path='inventories/inventory.ini',
                                                   project=project)
        inv_source.update_on_project_update = True

        project.update()
        utils.poll_until(lambda: inv_source.related.inventory_updates.get().count == 1, interval=.5, timeout=30)
        inv_update = inv_source.related.inventory_updates.get().results.pop()
        inv_update.related.cancel.post()
        assert inv_update.wait_until_completed().status == 'canceled'

        project.wait_until_completed().assert_successful()

    # Previously effected by https://github.com/ansible/awx/issues/171' for the 'OpenStack auth issue' permutation
    @pytest.mark.parametrize('scm_url, branch, source_path, expected_error',
                             [('https://github.com/ansible/test-playbooks.git', '', 'inventories/invalid_inventory.ini',
                               "Invalid section entry: '[syntax ?? error]'"),
                              ('https://github.com/ansible/test-playbooks.git', '',
                               'inventories/invalid_dyn_inventory.py',
                               'bad data for the host list'),
                              ('https://github.com/ansible/test-playbooks.git', '', 'not_a_source_path',
                               'Source does not exist'),
                              ('https://github.com/ansible/ansible.git', 'stable-2.6', 'contrib/inventory/ec2.py',
                               'Check your credentials'),
                              ('https://github.com/ansible/ansible.git', 'stable-2.6', 'contrib/inventory/openstack_inventory.py',
                               'Auth plugin requires parameters which were not given')],
                             ids=['invalid static', 'invalid dynamic', 'missing from project',
                                  'ec2 auth issue', 'OpenStack auth issue'])
    def test_failing_scm_inv_source_update_error_reporting(self, request, factories, scm_url, branch, source_path,
                                                           expected_error):
        project = factories.project(scm_url=scm_url, scm_branch=branch)
        scm_inv_source = factories.inventory_source(source='scm', project=project,
                                                       source_path=source_path, update_on_project_update=True)
        scm_inv_source.wait_until_completed()
        scm_inv_source.assert_status('failed')

        inv_update = scm_inv_source.related.inventory_updates.get().results.pop()
        inv_update.assert_text_in_stdout(expected_error, replace_newlines=' ')

        project_updates = project.related.project_updates.get(launch_type='sync').results
        assert len(project_updates) == 1
        project_updates[0].assert_successful()

    @pytest.mark.parametrize('source', ('custom', 'ec2'))
    def test_confirm_non_scm_inventory_source_disallows_scm_fields(self, factories, source):
        inv_src = factories.inventory_source(source=source)
        project = factories.project()

        for field, forbidden in [('source_project', lambda: inv_src.patch(source_project=project.id)),
                                 ('source_path', lambda: inv_src.patch(source_path='No!')),
                                 ('update_on_project_update', lambda: inv_src.patch(update_on_project_update=True))]:
            with pytest.raises(exc.BadRequest) as e:
                forbidden()
            assert e.value.msg == {'detail': ['Cannot set {} if not SCM type.'.format(field)]}

    def test_use_of_SCM_inventory_plugin(self, factories, ansible_version_cmp):
        if ansible_version_cmp('2.9.0') < 0:
            pytest.skip('Custom user plugins were not fixed until Ansible 2.9')
        inv_src = factories.inventory_source(
            source='scm',
            source_path='inventories/user_plugins/cow.yaml'
        )
        inv_src.update().wait_until_completed()
        imported_hosts = inv_src.ds.inventory.get_related('hosts')
        assert imported_hosts.count == 1
        assert imported_hosts.results[0].name == 'moooooo'

    def test_scm_inv_parent_sym_links(self, factories):
        """This test asserts that symlinks inside of a project source tree will
        be accessible for the ansible-inventory command in the inventory update.
        The inventory file is next to a group_vars/ directory that contains
        a symlink to a directory one higher than the directory that the
        inventory file is in.
        """
        project = factories.project(scm_url='https://github.com/AlanCoding/Ansible-inventory-file-examples.git')
        inventory = factories.inventory(organization=project.ds.organization)
        inv_src = factories.inventory_source(
            source='scm', inventory=inventory, project=project,
            source_path='scripts/symlinks/parent/foogroup.py'
        )

        inv_update = inv_src.update().wait_until_completed()
        inv_update.assert_successful()

        groups = inv_src.related.groups.get()
        assert groups['count'] == 1

        # Expectation is that the result matches the Ansible core CLI result
        # ansible-inventory -i scripts/symlinks/parent/foogroup.py --list --export
        # "foo": {
        #     "hosts": [
        #         "afoo"
        #     ],
        #     "vars": {
        #         "foovar": "fooval"  # from symlink in parent dir
        #     }
        # },
        group = groups.results[0]
        assert group.variables == {'foovar': 'fooval'}

    def test_scm_inv_using_collection_from_galaxy(self, factories, skip_if_pre_ansible29):
        pr_number = 83  # https://github.com/ansible/test-playbooks/pull/83
        # Closed pull request contents:
        # collections/requirements.yml
        # inventories/basic.yml
        # The inventory file 'basic.yml' references alancoding.basic.basic,
        # a collection that exists in Ansible Galaxy
        project = factories.project(
            name='Project alancoding.basic inventory collection requirement - %s' % fauxfactory.gen_utf8(),
            scm_type='git',
            scm_refspec=f"refs/pull/{pr_number}/head:refs/remotes/origin/pull/{pr_number}/head",
            scm_branch=f"pull/{pr_number}/head"
        )
        inventory = factories.inventory(organization=project.ds.organization)
        inv_src = factories.inventory_source(
            source='scm', inventory=inventory, project=project,
            source_path='inventories/basic.yml'
        )

        inv_update = inv_src.update().wait_until_completed()
        inv_update.assert_successful()

        assert inv_src.get_related('hosts').count == 4  # the number defined in the inventory file

    def test_scm_inv_using_relative_collection_via_config(self, factories):
        pr_number = 89  # https://github.com/ansible/test-playbooks/pull/89
        # Closed pull request contents:
        # my_collections/ansible_collections/farm/animals/plugins/inventory/cow.py
        # inventories/cow.yaml
        # ansible.cfg
        # The ansible.cfg file adds 'my_collections' to colleciton paths
        # 'cow.py' references 'farm.animals.cow' for inventory plugin
        project = factories.project(
            name='Project farm.animals.cow inventory relative collection - %s' % fauxfactory.gen_utf8(),
            scm_type='git',
            scm_refspec=f"refs/pull/{pr_number}/head:refs/remotes/origin/pull/{pr_number}/head",
            scm_branch=f"pull/{pr_number}/head"
        )
        inventory = factories.inventory(
            name='Sources farm.animals.cow relative collection inventory - %s' % fauxfactory.gen_utf8(),
            organization=project.ds.organization
        )
        inv_src = factories.inventory_source(
            source='scm', inventory=inventory, project=project,
            source_path='inventories/cow.yaml'
        )

        inv_update = inv_src.update().wait_until_completed()
        inv_update.assert_successful()

        hosts_pg = inv_src.get_related('hosts')
        assert hosts_pg.count == 1
        assert hosts_pg.results.pop().name == 'moooooo'
