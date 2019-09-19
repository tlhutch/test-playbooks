
from awxkit.config import config
from awxkit import utils

import pytest
import json
import os

from tests.api import APITest

TOWER_MODULES_PARAMS = [
    'common',
    'credential',
    'credential_type',
    'group',
    'host',
    'inventory',
    'inventory_source',
    'job_cancel',
    'job_launch',
    'job_list',
    'job_template',
    'job_wait',
    'label',
    'notification',
    'project',
    'project_manual',
    pytest.param('receive', marks=pytest.mark.serial),
    'role',
    'send',
    'settings',
    'team',
    'user',
    'workflow_template',
]


'''
Note: We include ansible + psutil in both environments so that the streams aren't crossed.
The streams get crossed when the ansible virtualenv contains a different version of python
than the version in the custom virtualenv. When a package is not found in the custom
virtualenv, the ansible virtualenv is the fallback virtualenv. This is problematic when
the python lib found doesn't support both versions of python.
Second Note: Collections were only added in Ansible 2.9, and are rapidly changing
with relevant fixes as of the time this was written, so the current version is used.
'''
CUSTOM_VENVS = [
    {
        'name': 'python2_tower_modules',
        'packages': 'ansible-tower-cli psutil git+https://github.com/ansible/ansible.git',
        'python_interpreter': 'python2'
    },
    {
        'name': 'python3_tower_modules',
        'packages': 'ansible-tower-cli psutil git+https://github.com/ansible/ansible.git',
        'python_interpreter': 'python36'
    },
]


CUSTOM_VENVS_NAMES = [venv['name'] for venv in CUSTOM_VENVS]


@pytest.fixture(scope='module')
def os_python_version(session_ansible_python):
    """Return the Tower base OS Python version."""
    return session_ansible_python['version']['major']


@pytest.fixture(autouse=True)
def skip_if_wrong_python(request, os_python_version, is_docker):
    """Skip when the venv python version does not match the OS base Python
    version.

    This is to avoid getting the test failed because Python 3 on RHEL7 doens't
    have libsexlinux-python available.
    """
    python_venv_name = request.getfixturevalue('python_venv_name')
    if not python_venv_name.startswith(f'python{os_python_version}') and not is_docker:
        pytest.skip(f'OS Python version is {os_python_version} which does not match venv')


@pytest.fixture
def tower_credential(factories):
    return factories.credential(kind='tower', username=config.credentials.default.username,
                                password=config.credentials.default.password, host=config.base_url)


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs')
@pytest.mark.parametrize('python_venv_name', CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Modules_via_Playbooks(APITest):
    @pytest.mark.parametrize('tower_module', TOWER_MODULES_PARAMS)
    def test_ansible_tower_module(self, factories, tower_module, project, tower_credential, venv_path, python_venv_name, is_cluster):
        """
        Ansible modules that interact with Tower live in an Ansible Collection.
        This test invokes the integration tests that ran in Ansible core CI
        before it was split out into a standalone collection.
        """
        if is_cluster and tower_module == 'project_manual':
            pytest.skip(
                'Manual projects are discouraged in general, specially on cluster deployments.'
            )

        virtual_env_path = venv_path(python_venv_name)

        extra_vars = {
            'tower_module_under_test': tower_module,
            'ansible_python_interpreter': os.path.join(virtual_env_path, 'bin/python'),
        }
        jt = factories.job_template(project=project, playbook='tower_modules/wrapper.yml',
                                    extra_vars=json.dumps(extra_vars), verbosity=5)
        jt.add_credential(tower_credential)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch().wait_until_completed()

        job.assert_successful()


@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs')
@pytest.mark.parametrize('python_venv_name', CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Modules(APITest):
    def run_tower_module(self, module_name, module_args, factories, virtual_env_path=None, more_vars=None):
        extra_vars = {
            'module_name': module_name,
            'module_args': module_args,
        }
        if virtual_env_path:
            extra_vars['ansible_python_interpreter'] = os.path.join(virtual_env_path, 'bin/python')
        if more_vars:
            extra_vars.update(more_vars)

        jt = factories.job_template(
            playbook='invoke_x.yml', extra_vars=json.dumps(extra_vars), verbosity=5
        )
        jt.add_credential(factories.credential(
            kind='tower',
            username=config.credentials.default.username,
            password=config.credentials.default.password,
            host=config.base_url
        ))
        if virtual_env_path:
            jt.custom_virtualenv = virtual_env_path
        job = jt.launch()
        job.wait_until_completed()
        job.assert_successful()
        return job

    def test_ansible_tower_fully_qualified_collection_name(self, factories, venv_path, python_venv_name, ansible_collections_path, is_docker, request, update_setting_pg, v2):
        if is_docker:
            jobs_settings = v2.settings.get().get_endpoint('jobs')
            prev_proot_show_paths = jobs_settings.AWX_PROOT_SHOW_PATHS
            jobs_settings.AWX_PROOT_SHOW_PATHS = prev_proot_show_paths + [ansible_collections_path]
            request.addfinalizer(lambda: jobs_settings.patch(AWX_PROOT_SHOW_PATHS=prev_proot_show_paths))
        org = factories.organization()
        # TODO: update module name to "awx.awx.tower_organization" when modules are fully migrated
        # or maybe "awx.awx.organization", still not fully decided
        # no assertion here because only testing that job was successful
        self.run_tower_module(
            'chrismeyersfsu.tower_modules.tower_organization', {'name': org.name},
            factories, venv_path(python_venv_name)
        )

    def test_ansible_tower_module_organization_create(self, request, v2, factories, venv_path, python_venv_name):
        org_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.organizations.get(name=org_name).results[0].delete())
        self.run_tower_module('tower_organization', {
            'name': org_name,
            'description': 'hello world',
        }, factories, venv_path(python_venv_name))

        org = v2.organizations.get(name=org_name).results[0]
        assert org_name == org['name']
        assert org['description'] == 'hello world'

    def test_ansible_tower_module_organization_delete(self, factories, v2, venv_path, python_venv_name):
        org = factories.organization()
        self.run_tower_module('tower_organization', {
            'name': org.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.organizations.get(name=org.name).results)

    def test_ansible_tower_module_organization_check_mode(self, factories, tower_version, venv_path, python_venv_name):
        '''
        Ensure that orgnization check_mode: True returns the tower_version
        '''
        org = factories.organization()
        job = self.run_tower_module(
            'tower_organization', {'name': org.name}, factories, venv_path(python_venv_name),
            more_vars={'check_mode': True}
        )

        job_event = job.get_related('job_events').get(event='runner_on_ok', task='invoke_arbitrary_module').results[0]
        module_tower_version = job_event['event_data']['res']['tower_version']

        assert tower_version == module_tower_version

    def test_ansible_tower_module_project_create(self, request, v2, factories, venv_path, python_venv_name, organization):
        proj_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.projects.get(name=proj_name).results[0].delete())
        self.run_tower_module('tower_project', {
            'name': proj_name,
            'description': 'hello world',
            'scm_type': 'git',
            'scm_url': 'git@github.com:ansible/test-playbooks.git',
            'organization': organization.name,
        }, factories, venv_path(python_venv_name))

        proj = v2.projects.get(name=proj_name).results[0]
        proj.related.project_updates.get().results[0].wait_until_completed()
        assert proj_name == proj['name']
        assert proj['description'] == 'hello world'
        assert proj['scm_type'] == 'git'
        assert proj['scm_url'] == 'git@github.com:ansible/test-playbooks.git'
        assert proj['organization'] == organization.id

    def test_ansible_tower_module_project_delete(self, factories, v2, venv_path, python_venv_name):
        proj = factories.project()
        self.run_tower_module('tower_project', {
            'name': proj.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.projects.get(name=proj.name).results)

    def test_ansible_tower_module_credential_create(self, request, v2, factories, venv_path, python_venv_name, organization):
        cred_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.credentials.get(name=cred_name).results[0].delete())
        self.run_tower_module('tower_credential', {
            'name': cred_name,
            'description': 'hello world',
            'kind': 'ssh',
            'organization': organization.name,
        }, factories, venv_path(python_venv_name))

        cred = v2.credentials.get(name=cred_name).results[0]
        assert cred_name == cred['name']
        assert cred['description'] == 'hello world'
        assert cred['kind'] == 'ssh'
        assert cred['organization'] == organization.id

    def test_ansible_tower_module_credential_delete(self, factories, v2, venv_path, python_venv_name):
        cred = factories.credential()
        self.run_tower_module('tower_credential', {
            'name': cred.name,
            'state': 'absent',
            'kind': cred.kind,
            'organization': cred.summary_fields.organization.name
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.credentials.get(name=cred.name).results)

    def test_ansible_tower_module_credential_type_create(self, request, v2, factories, venv_path, python_venv_name, organization):
        cred_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.credential_types.get(name=cred_name).results[0].delete())
        self.run_tower_module('tower_credential_type', {
            'name': cred_name,
            'description': 'hello world',
            'kind': 'cloud',
        }, factories, venv_path(python_venv_name))

        cred = v2.credential_types.get(name=cred_name).results[0]
        assert cred_name == cred['name']
        assert cred['description'] == 'hello world'
        assert cred['kind'] == 'cloud'

    def test_ansible_tower_module_credential_type_delete(self, factories, v2, venv_path, python_venv_name):
        cred = factories.credential_type()
        self.run_tower_module('tower_credential_type', {
            'name': cred.name,
            'state': 'absent',
            'kind': cred.kind,
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.credential_types.get(name=cred.name).results)

    def test_ansible_tower_module_group_create(self, request, v2, factories, venv_path, python_venv_name):
        group_name = utils.random_title()
        inv = factories.inventory()
        request.addfinalizer(lambda *args: v2.groups.get(name=group_name).results[0].delete())
        self.run_tower_module('tower_group', {
            'name': group_name,
            'description': 'hello world',
            'inventory': inv.name
        }, factories, venv_path(python_venv_name))

        group = v2.groups.get(name=group_name).results[0]
        assert group_name == group['name']
        assert group['description'] == 'hello world'
        assert group['inventory'] == inv.id

    def test_ansible_tower_module_group_delete(self, factories, v2, venv_path, python_venv_name):
        group = factories.group()
        self.run_tower_module('tower_group', {
            'name': group.name,
            'inventory': group.summary_fields.inventory.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.groups.get(name=group.name).results)

    def test_ansible_tower_module_host_create(self, request, v2, factories, venv_path, python_venv_name):
        host_name = utils.random_title()
        inv = factories.inventory()
        request.addfinalizer(lambda *args: v2.hosts.get(name=host_name).results[0].delete())
        self.run_tower_module('tower_host', {
            'name': host_name,
            'description': 'hello world',
            'inventory': inv.name
        }, factories, venv_path(python_venv_name))

        host = v2.hosts.get(name=host_name).results[0]
        assert host_name == host['name']
        assert host['description'] == 'hello world'
        assert host['inventory'] == inv.id

    def test_ansible_tower_module_host_delete(self, factories, v2, venv_path, python_venv_name):
        host = factories.host()
        self.run_tower_module('tower_host', {
            'name': host.name,
            'inventory': host.summary_fields.inventory.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.hosts.get(name=host.name).results)

    def test_ansible_tower_module_inventory_create(self, request, v2, factories, venv_path, python_venv_name):
        inventory_name = utils.random_title()
        org = factories.organization()
        request.addfinalizer(lambda *args: v2.inventory.get(name=inventory_name).results[0].delete())
        self.run_tower_module('tower_inventory', {
            'name': inventory_name,
            'description': 'hello world',
            'organization': org.name
        }, factories, venv_path(python_venv_name))

        inventory = v2.inventory.get(name=inventory_name).results[0]
        assert inventory_name == inventory['name']
        assert inventory['description'] == 'hello world'
        assert inventory['organization'] == org.id

    def test_ansible_tower_module_inventory_delete(self, factories, v2, venv_path, python_venv_name):
        inventory = factories.inventory()
        self.run_tower_module('tower_inventory', {
            'name': inventory.name,
            'organization': inventory.summary_fields.organization.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        assert 0 == len(v2.inventory.get(name=inventory.name).results)

    def test_ansible_tower_module_job(self, request, factories, v2, venv_path, python_venv_name):
        jt_name = utils.random_title()
        project = factories.project()
        inventory = factories.inventory()
        factories.host(inventory=inventory, variables=dict(ansible_host='localhost', ansible_connection='local'))

        # We need this to teardown the JT if it fails before the end. The try
        # block also means it wont fail if we get to the end and clean up the
        # JT as part of the test
        def cleanup_jt():
            try:
                return v2.job_templates.get(name=jt_name).results[0].delete()
            except:
                print("failed to remove JT in teardown")

        request.addfinalizer(cleanup_jt)
        self.run_tower_module('tower_job_template', {
            'name': jt_name,
            'description': 'hello world',
            'job_type': 'run',
            'inventory': inventory.name,
            'playbook': 'sleep.yml',
            'project': project.name,
        }, factories, venv_path(python_venv_name))

        jt = v2.job_templates.get(name=jt_name).results[0]
        assert jt_name == jt['name']
        assert jt['description'] == 'hello world'
        assert jt['job_type'] == 'run'
        assert jt['inventory'] == inventory.id
        assert jt['playbook'] == 'sleep.yml'
        assert jt['project'] == project.id

        # Launch the JT we just built
        self.run_tower_module('tower_job_launch', {
            'job_template': jt_name,
        }, factories, venv_path(python_venv_name))

        job = v2.jobs.get(name=jt_name).results[0]
        assert job.summary_fields.job_template.name == jt_name

        job_id1 = job.id

        # Cancel the job we just launched
        self.run_tower_module('tower_job_cancel', {
            'job_id': job_id1,
        }, factories, venv_path(python_venv_name))

        job = v2.jobs.get(id=job_id1).results[0]
        assert job.summary_fields.job_template.name == jt_name
        assert job.status == "canceled"

        # Launch another job
        self.run_tower_module('tower_job_launch', {
            'job_template': jt_name,
        }, factories, venv_path(python_venv_name))

        job = v2.jobs.get(name=jt_name).results[1]
        assert job.summary_fields.job_template.name == jt_name

        job_id2 = job.id

        # Sanity check
        assert job_id1 != job_id2

        # Wait for the job we just launched
        self.run_tower_module('tower_job_wait', {
            'job_id': job_id2,
        }, factories, venv_path(python_venv_name))

        job = v2.jobs.get(id=job_id2).results[0]
        assert job.summary_fields.job_template.name == jt_name
        assert job.status == "successful"

        # List jobs
        # I'm not entirely sure how to test this better
        job_output = self.run_tower_module('tower_job_list', {}, factories,
                venv_path(python_venv_name)).wait_until_completed()

        # Basic test
        assert job_output.status == 'successful'

        # Remove our job template
        self.run_tower_module('tower_job_template', {
            'name': jt_name,
            'job_type': 'run',
            'inventory': inventory.name,
            'playbook': 'sleep.yml',
            'project': project.name,
            'state': 'absent',
        }, factories, venv_path(python_venv_name))

        job_templates = v2.job_templates.get(name=jt_name).results
        assert len(job_templates) == 0
