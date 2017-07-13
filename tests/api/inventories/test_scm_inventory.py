from towerkit.exceptions import NoContent
from towerkit.utils import suppress
from towerkit.config import config
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSCMInventory(Base_Api_Test):

    def hostnames_from_group_prefixes(self, prefixes):
        host_suffixes = ['host_0{}'.format(i) for i in range(1, 6)]

        hostnames = set()
        for prefix in prefixes:
            for host in host_suffixes:
                hostnames.add('{0}_{1}'.format(prefix, host))
        return hostnames

    @pytest.fixture(scope='class', params=['inventories/inventory.ini', 'inventories/dyn_inventory.py'])
    def scm_inventory_source_with_group_and_host_var_dirs(self, request, class_factories):
        inventory_source = class_factories.v2_inventory_source(source='scm', source_path=request.param)
        assert inventory_source.update().wait_until_completed().is_successful
        inventory_source.ds.inventory.get()
        return inventory_source.get()

    def test_scm_inventory_hosts_and_host_vars(self, scm_inventory_source_with_group_and_host_var_dirs):
        inventory_source = scm_inventory_source_with_group_and_host_var_dirs
        inventory = inventory_source.ds.inventory
        hosts = inventory.related.hosts.get(page_size=200).results

        desired_hosts = self.hostnames_from_group_prefixes(['ungrouped', 'group_one', 'group_one_and_two',
                                                            'group_one_two_and_three', 'group_two',
                                                            'group_two_and_three', 'group_three'])
        assert set([host.name for host in hosts]) == desired_hosts

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

        for host in hosts:
            for host_vars in [host.variables, host.related.variable_data.get()]:
                assert host_vars.inventories_var

    def test_scm_inventory_groups_and_group_vars(self, scm_inventory_source_with_group_and_host_var_dirs):
        inventory_source = scm_inventory_source_with_group_and_host_var_dirs
        inventory = inventory_source.ds.inventory
        groups = inventory.related.groups.get().results
        desired_groups = set(['group_one', 'group_two', 'group_three'])
        assert set([group.name for group in groups]) == desired_groups

        group_one = inventory.related.groups.get(name='group_one').results.pop()

        group_one_hosts = group_one.related.hosts.get(page_size=200).results

        desired_hosts = self.hostnames_from_group_prefixes(['group_one', 'group_one_and_two',
                                                            'group_one_two_and_three'])
        assert set([host.name for host in group_one_hosts]) == desired_hosts

        for host in group_one_hosts:
            for host_vars in [host.variables, host.related.variable_data.get()]:
                assert host_vars.is_in_group_one
                assert host_vars.group_one_should_have_this_var
                assert 'group_one_should_not_have_this_var' not in host_vars

        group_two = inventory.related.groups.get(name='group_two').results.pop()

        group_two_hosts = group_two.related.hosts.get(page_size=200).results

        desired_hosts = self.hostnames_from_group_prefixes(['group_two', 'group_one_and_two',
                                                            'group_two_and_three', 'group_one_two_and_three'])
        assert set([host.name for host in group_two_hosts]) == desired_hosts

        for host in group_two_hosts:
            for host_vars in [host.variables, host.related.variable_data.get()]:
                assert host_vars.is_in_group_two

        group_three = inventory.related.groups.get(name='group_three').results.pop()

        group_three_hosts = group_three.related.hosts.get(page_size=200).results
        desired_hosts = self.hostnames_from_group_prefixes(['group_three', 'group_two_and_three',
                                                            'group_one_two_and_three'])
        assert set([host.name for host in group_three_hosts]) == desired_hosts

        for host in group_three_hosts:
            for host_vars in [host.variables, host.related.variable_data.get()]:
                assert host_vars.is_in_group_three

    @pytest.mark.parametrize('source_path', ['inventories/inventory.ini', 'inventories/dyn_inventory.py'])
    def test_update_on_project_update_with_scm_change(self, ansible_runner, factories, v2, source_path):
        """Verifies that an scm inventory sync runs after running a job that commits code to an upstream repo"""
        inputs = dict(fields=[dict(id='git_key', label='Git Key', format='ssh_private_key', secret=True)])
        injectors = dict(file=dict(template="{{ git_key }}"),
                         env=dict(GIT_AUTHOR_NAME='Tower Testing', GIT_AUTHOR_EMAIL='tower@qe.com',
                                  GIT_COMMITTER_NAME='Tower Testing', GIT_COMMITTER_EMAIL='tower@qe.com',
                                  GIT_KEY="{{tower.filename}}"))
        cred_type = factories.credential_type(inputs=inputs, injectors=injectors)
        pk = config.credentials.scm.rmfitzpatrick_ansible_playbooks.ssh_key_data
        git_cred = factories.v2_credential(credential_type=cred_type, inputs=dict(git_key=pk))
        project = factories.v2_project(scm_url='https://github.com/rmfitzpatrick/ansible-playbooks.git',
                                       scm_branch='inventory_additions')
        assert project.related.project_updates.get(launch_type='manual').count == 1

        inventory_source = factories.v2_inventory_source(source='scm', project=project,
                                                         source_path=source_path,
                                                         update_on_project_update=True)
        inventory_source.wait_until_completed()

        jt = factories.v2_job_template(inventory=inventory_source.ds.inventory, project=project,
                                       playbook='utils/trigger_update.yml', limit='ungrouped_host_01')
        jt.add_extra_credential(git_cred)
        assert jt.launch().wait_until_completed().is_successful

        assert project.related.project_updates.get(launch_type='manual').count == 2
        assert inventory_source.related.inventory_updates.get().count == 1

        with suppress(NoContent):
            inventory_source.related['update'].post()

        project.wait_until_completed()
        inventory_source.wait_until_completed()
        assert project.related.project_updates.get(launch_type='manual').count == 3
        assert inventory_source.related.inventory_updates.get().count == 2

    @pytest.mark.parametrize('source_path', ['inventories/inventory.ini', 'inventories/dyn_inventory.py'])
    def test_update_on_project_update_without_scm_change(self, factories, source_path):
        project = factories.v2_project()
        assert project.related.project_updates.get(launch_type='manual').count == 1
        inventory_source = factories.v2_inventory_source(source='scm', project=project,
                                                         source_path=source_path,
                                                         update_on_project_update=True)
        assert inventory_source.wait_until_completed().is_successful
        assert project.related.project_updates.get(launch_type='manual').count == 2
        assert inventory_source.related.inventory_updates.get().count == 1

        with suppress(NoContent):
            inventory_source.related['update'].post()

        project.wait_until_completed()
        assert project.related.project_updates.get(launch_type='manual').count == 3
        assert inventory_source.related.inventory_updates.get().count == 1

    def test_custom_credential_affects_ansible_env(self, factories, scm_inventory_source_with_group_and_host_var_dirs):
        inventory_source = scm_inventory_source_with_group_and_host_var_dirs
        inventory = inventory_source.ds.inventory
        host = inventory.related.hosts.get(name='ungrouped_host_01').results.pop()

        inputs = dict(fields=[dict(id='env_var', label='ENV_VAR')])
        injectors = dict(env=dict(ENV_VAR='{{ env_var }}'))
        cred_type = factories.credential_type(kind='cloud', inputs=inputs, injectors=injectors)
        env_var = 'THIS_IS_A_TEST_ENV_VAR'
        cred = factories.v2_credential(credential_type=cred_type, inputs=dict(env_var=env_var))

        jt = factories.v2_job_template(inventory=inventory, project=inventory_source.ds.project, limit=host.name,
                                       playbook='ansible_env.yml')
        jt.add_extra_credential(cred)
        job = jt.launch().wait_until_completed()
        assert job.is_successful

        event = job.related.job_events.get(host=host.id, task='debug').results.pop()
        ansible_env = event.event_data.res.ansible_env
        assert ansible_env.ENV_VAR == env_var
