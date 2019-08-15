from datetime import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta

import pytest
from awxkit.exceptions import BadRequest
from tests.lib.rrule import RRule
from awxkit.utils import (poll_until, random_title)

from tests.api import APITest
from tests.lib.helpers.workflow_utils import (WorkflowTree, WorkflowTreeMapper)


@pytest.mark.usefixtures('authtoken', 'skip_if_cluster')
class TestCustomVirtualenv(APITest):

    @pytest.fixture
    def venv_root(self, is_docker):
        if is_docker:
            return '/venv'
        return '/var/lib/awx/venv'

    @pytest.mark.serial
    def test_default_venv(self, v2, venv_path, is_docker):
        expect = [venv_path()]
        if is_docker:
            # development environment also ships with a python3 custom venv
            # that is not necessary but to provide developers with the option to use it
            expect.append(venv_path().replace('ansible', 'ansible3'))
        found = [str(venv_found) for venv_found in v2.config.get().custom_virtualenvs]
        assert found.sort() == expect.sort()

    def test_default_venv_can_be_sourced(self, v2, factories, venv_path):
        jt = factories.job_template()
        jt.custom_virtualenv = venv_path()
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert job.job_env['VIRTUAL_ENV'].rstrip('/') == job.custom_virtualenv.rstrip('/') == venv_path().rstrip('/')

    def test_cannot_associate_invalid_venv_path_with_resource(self, v2, factories, create_venv, venv_path,
                                                              venv_root, get_resource_from_jt):
        folder_names = [random_title(non_ascii=False) for _ in range(2)]
        malformed_venvs = ('foo',
                           '/',
                           '/tmp',
                           '[]',
                           '()',
                           '{}/'.format(venv_root),
                           '/var/lib /awx/venv/{}/'.format(folder_names[0]),
                           '{}/{}'.format(venv_root, folder_names[0][:-1]),
                           '{}/{}/foo'.format(venv_root, folder_names[0]),
                           '{}/{}/foo/'.format(venv_root, folder_names[0]),
                           folder_names[0],
                           '/{}'.format(folder_names[0]),
                           '/{}/'.format(folder_names[0]),
                           '{0}/{1}/ {0}/{2}/'.format(venv_root, folder_names[0], folder_names[1]),
                           '{0}/{1} {0}/{2}'.format(venv_root, folder_names[0], folder_names[1]),
                           '[{0}/{1}/, {0}/{2}/]'.format(venv_root, folder_names[0], folder_names[1]),
                           '({0}/{1}/, {0}/{2}/)'.format(venv_root, folder_names[0], folder_names[1]))
        jt = factories.job_template()

        with create_venv(folder_names[0]):
            with create_venv(folder_names[1]):
                poll_until(lambda: all([path in v2.config.get().custom_virtualenvs
                                        for path in (venv_path(folder_names[0]), venv_path(folder_names[1]))]),
                           interval=1, timeout=15)
                for resource_type in ('job_template', 'project', 'organization'):
                    resource = get_resource_from_jt(jt, resource_type)
                    for path in malformed_venvs:
                        with pytest.raises(BadRequest):
                            resource.custom_virtualenv = path

    def test_can_associate_valid_venv_path_with_resource(self, v2, factories, create_venv, venv_path,
                                                         venv_root, get_resource_from_jt):
        folder_name = random_title(non_ascii=False)
        valid_venvs = ('{}/{}'.format(venv_root, folder_name),
                       '{}/{}/'.format(venv_root, folder_name),
                       '')
        jt = factories.job_template()

        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            for resource_type in ('job_template', 'project', 'organization'):
                resource = get_resource_from_jt(jt, resource_type)
                for path in valid_venvs:
                    resource.custom_virtualenv = path

    @pytest.mark.parametrize('python_interpreter', [None, 'python2', 'python3'])
    def test_run_job_using_venv_with_required_packages(self, v2, factories, create_venv,
                                                       venv_path, python_interpreter, ansible_adhoc):
        folder_name = random_title(non_ascii=False)
        if python_interpreter:
            folder_name.rstrip('/')
            folder_name += '_' + python_interpreter
        if python_interpreter == 'python3':
            contacted = ansible_adhoc()['tower[0]'].command('which python3')
            for host, result in contacted.items():
                if result['rc'] != 0:
                    pytest.skip('python3 is not installed on host.')
        with create_venv(folder_name, packages='psutil ansible', use_python=python_interpreter):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            host = factories.host(
                variables=dict(ansible_host='127.0.0.1', ansible_connection='local', ansible_python_interpreter='%s/bin/python' % venv_path(folder_name))
            )
            jt = factories.job_template(inventory=host.ds.inventory)
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')

    def test_run_inventory_update_using_venv_with_required_packages(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        inv_src = factories.inventory_source(source='scm', source_path='inventories/linode.yml')
        ansigit = 'git+https://github.com/ansible/ansible.git'
        with create_venv(folder_name, 'psutil {} linode_api4'.format(ansigit)):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            assert inv_src.custom_virtualenv is None
            inv_src.custom_virtualenv = venv_path(folder_name)
            iu = inv_src.update().wait_until_completed()
            assert iu.custom_virtualenv.rstrip('/') == venv_path(folder_name).rstrip('/')
            assert iu.status == 'failed'
            output = iu.result_stdout
            if not isinstance(output, type(u'')):
                output = output.decode('utf-8')
            assert (
                'No setting was provided for required configuration plugin_type: '
                'inventory plugin: linode setting: access_token' in output.replace('\n', ' ')  # Can't trust the line breaks
            ), output
            iu.get()
            assert iu.job_args[iu.job_args.index('--venv') + 1].rstrip('/') == venv_path(folder_name).rstrip('/')

    @pytest.mark.parametrize('resource_pair', [('organization', 'project'), ('organization', 'job_template'),
                                               ('project', 'job_template')],
                             ids=['org and project', 'org and jt', 'project and jt'])
    def test_venv_resource_hierarchy(self, v2, factories, create_venv, resource_pair, venv_path, get_resource_from_jt):
        folder_names = [random_title(non_ascii=False) for _ in range(2)]
        with create_venv(folder_names[0]):
            with create_venv(folder_names[1]):
                poll_until(lambda: all([path in v2.config.get().custom_virtualenvs
                                        for path in (venv_path(folder_names[0]), venv_path(folder_names[1]))]),
                           interval=1, timeout=15)
                jt = factories.job_template()
                jt.ds.inventory.add_host()

                for i in range(2):
                    resource = get_resource_from_jt(jt, resource_pair[i])
                    assert resource.custom_virtualenv is None
                    resource.custom_virtualenv = venv_path(folder_names[i])

                job = jt.launch().wait_until_completed()
                job.assert_successful()
                assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_names[1]).rstrip('/')

    @pytest.mark.parametrize('ansible_version', ['2.6.1', '2.5.6', '2.4.6.0', '2.3.3.0'])
    def test_venv_with_ansible(self, v2, factories, create_venv, ansible_version, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name, 'psutil ansible=={}'.format(ansible_version)):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template(playbook='run_command.yml', extra_vars='{"command": "ansible --version"}')
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            job_events = job.related.job_events.get().results

            event = [e for e in job_events if e.task == 'command' and e.event == 'runner_on_ok'].pop()
            stdout = event.event_data.res.stdout
            assert 'ansible {}'.format(ansible_version) in stdout

            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == job.custom_virtualenv.rstrip('/') == venv_path(folder_name).rstrip('/')

    @pytest.mark.serial
    def test_custom_venv_path_setting(self, v2, factories, create_venv, venv_path, update_setting_pg):
        folder_name = random_title(non_ascii=False)
        custom_venv_base = '/tmp'
        custom_venv_path = venv_path(folder_name, custom_venv_base)
        with create_venv(folder_name, 'python-memcached psutil ansible', custom_venv_base=custom_venv_base):
            update_setting_pg(
                v2.settings.get().get_endpoint('system'),
                dict(CUSTOM_VENV_PATHS=[custom_venv_base])
            )
            poll_until(lambda: custom_venv_path in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template(playbook='run_command.yml', extra_vars='{"command": "ansible --version"}')
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = custom_venv_path
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == job.custom_virtualenv.rstrip('/') == custom_venv_path.rstrip('/')

    @pytest.mark.serial
    def test_custom_venv_path_setting_remove_cant_launch(self, v2, factories, create_venv, venv_path, update_setting_pg):
        folder_name = random_title(non_ascii=False)
        custom_venv_base = '/tmp'
        custom_venv_path = venv_path(folder_name, custom_venv_base)

        with create_venv(folder_name, 'psutil ansible', custom_venv_base=custom_venv_base):
            update_setting_pg(
                v2.settings.get().get_endpoint('system'),
                dict(CUSTOM_VENV_PATHS=[custom_venv_base])
            )

            poll_until(lambda: custom_venv_path in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template(playbook='run_command.yml', extra_vars='{"command": "ansible --version"}')
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = custom_venv_path
            job = jt.launch().wait_until_completed()
            job.assert_successful()

            v2.settings.get().get_endpoint('system').delete()
            job = jt.launch().wait_until_completed()
            assert job.status == 'error'
            assert 'Invalid virtual environment selected' in job.job_explanation

    def test_venv_with_missing_requirements(self, v2, factories, create_venv, ansible_version, venv_path, venv_root):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name, ''):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            assert job.status == 'failed'
            assert job.job_explanation == ''
            possible_error_msgs = [
                'ERROR! Unexpected Exception, this is probably a bug: No module named psutil',  # python2 error message
                "ERROR! Unexpected Exception, this is probably a bug: No module named 'psutil'"  # python3 error message
            ]
            assert any(msg in job.result_stdout for msg in possible_error_msgs), (
                'Could not find any of {} in job standard out: \n{}'.format(possible_error_msgs, job.result_stdout)
            )

    def test_relaunched_jobs_use_venv_specified_on_jt_at_launch_time(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')

            relaunched_job = job.relaunch().wait_until_completed()
            assert relaunched_job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')

            # Per https://github.com/ansible/tower/issues/2844,
            # venv is a property of the job, not a value in time that is persisted.
            # Relaunched job should source whatever venv is set on the JT at launch time.
            jt.custom_virtualenv = venv_path()
            relaunched_job = job.relaunch().wait_until_completed()
            assert relaunched_job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path().rstrip('/')

    def test_relaunched_jobs_fail_when_venv_no_longer_exists(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

        poll_until(lambda: venv_path(folder_name) not in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
        assert jt.get().custom_virtualenv.rstrip('/') == venv_path(folder_name).rstrip('/')
        job = jt.launch().wait_until_completed()
        assert job.status == 'error'
        assert 'Invalid virtual environment selected: {}'.format(venv_path(folder_name)) in job.job_explanation

    def test_workflow_job_node_sources_venv(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

            wfjt = factories.workflow_job_template()
            factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
            wf_job = wfjt.launch().wait_until_completed()
            wf_job.assert_successful()
            wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
            job = wf_job_node.related.job.get()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')

    def test_only_workflow_node_with_custom_venv_sources_venv(self, v2, factories, create_venv, venv_path):
        """Workflow:
         - n1                   <--- default venv
          - (always) n2         <--- custom venv
            - (success) n3      <--- default venv
        """
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt_with_venv = factories.job_template()
            jt_with_venv.ds.inventory.add_host()
            jt_with_venv.custom_virtualenv = venv_path(folder_name)

            wfjt = factories.workflow_job_template()
            n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
            n2 = n1.related.always_nodes.post(dict(unified_job_template=jt_with_venv.id))
            n3 = n2.related.success_nodes.post(dict(unified_job_template=jt.id))
            wf_job = wfjt.launch().wait_until_completed()
            wf_job.assert_successful()

            # map nodes to job nodes
            tree = WorkflowTree(wfjt)
            job_tree = WorkflowTree(wf_job)
            mapping = WorkflowTreeMapper(tree, job_tree).map()

            assert mapping, "Failed to map WFJT to WFJ.\n\nWFJT:\n{0}\n\nWFJ:\n{1}".format(tree, job_tree)
            n1_job_node, n2_job_node, n3_job_node = [v2.workflow_job_nodes.get(id=mapping[n.id]).results.pop()
                                                     for n in (n1, n2, n3)]
            n1_job, n2_job, n3_job = [job_node.related.job.get() for job_node in
                                      (n1_job_node, n2_job_node, n3_job_node)]
            for job in (n1_job, n2_job, n3_job):
                job.assert_successful()

            assert n1_job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path().rstrip('/')
            assert n2_job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')
            assert n3_job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path().rstrip('/')

    def test_scheduled_job_uses_venv_associated_with_resource(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

            dtstart = datetime.utcnow() + relativedelta(seconds=-30)
            minutely_rrule = RRule(rrule.MINUTELY, dtstart=dtstart)
            schedule = jt.add_schedule(rrule=minutely_rrule)

            unified_jobs = schedule.related.unified_jobs.get()
            poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
            job = unified_jobs.results.pop()
            job.wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')

    @pytest.mark.parametrize('resource_type', ['project', 'job_template'])
    def test_venv_preserved_by_copied_resource(self, v2, factories, create_venv, copy_with_teardown, resource_type,
                                               venv_path, get_resource_from_jt):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.job_template()
            jt.ds.inventory.add_host()
            resource = get_resource_from_jt(jt, resource_type)
            resource.custom_virtualenv = venv_path(folder_name)

            copied_resource = copy_with_teardown(resource)
            assert copied_resource.custom_virtualenv.rstrip('/') == venv_path(folder_name).rstrip('/')

            if resource_type == 'project':
                update = copied_resource.related.project_updates.get().results.pop()
                update.wait_until_completed().assert_successful()
                jt.project = copied_resource.id
            elif resource_type == 'job_template':
                jt = copied_resource

            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'].rstrip('/') == venv_path(folder_name).rstrip('/')


CUSTOM_VENVS = [
                {
                'name': 'python2_ansible23',
                'packages': 'psutil ansible==2.3',
                'python_interpreter': 'python2'
                },
                {
                'name': 'python2_ansibledevel',
                'packages': 'psutil git+https://github.com/ansible/ansible.git',
                'python_interpreter': 'python2'
                },
                ]


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures(
    'authtoken',
    'skip_if_not_traditional_cluster',
    'shared_custom_venvs'
    )
@pytest.mark.serial
class TestCustomVirtualenvTraditionalCluster(APITest):

    def test_custom_venvs_exist(self, v2, venv_path, is_docker):
        expected = [venv_path(env['name']) for env in CUSTOM_VENVS]
        if is_docker:
            # development environment also ships with a python3 custom venv
            # that is not necessary but to provide developers with the option to use it
            expected.append(venv_path().replace('ansible', 'ansible3'))
        found = [str(venv_found) for venv_found in v2.config.get().custom_virtualenvs]
        for env in expected:
            assert env in found

    @pytest.mark.parametrize('venv_info', CUSTOM_VENVS, ids=[env['name'] for env in CUSTOM_VENVS])
    def test_default_venv_can_be_sourced(self, v2, factories, venv_path, venv_info):
        jt = factories.job_template()
        jt.custom_virtualenv = venv_path(venv_info['name'])
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert job.job_env['VIRTUAL_ENV'].rstrip('/') == job.custom_virtualenv.rstrip('/') == venv_path(venv_info['name']).rstrip('/')
