
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


# FIXME Remove "skip_if_cluster" fixture. We must skip if cluster right now
# because the node we're installing awx collection on doesn't have access to
# the tower repo in a cluster deployment.
@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_pre_ansible29', 'skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs', 'skip_if_cluster')
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
            'collection_id': 'awx.awx'  # TODO: change if testing ansible.tower
        }
        jt = factories.job_template(project=project, playbook='tower_modules/wrapper.yml',
                                    extra_vars=json.dumps(extra_vars), verbosity=5)
        jt.add_credential(tower_credential)
        jt.custom_virtualenv = virtual_env_path
        job = jt.launch().wait_until_completed()

        job.assert_successful()


# FIXME Remove "skip_if_cluster" fixture. We must skip if cluster right now
# because the node we're installing awx collection on doesn't have access to
# the tower repo in a cluster deployment.
@pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
@pytest.mark.usefixtures('skip_if_pre_ansible29', 'skip_if_openshift', 'authtoken', 'tower_modules_collection', 'shared_custom_venvs', 'skip_if_cluster')
@pytest.mark.parametrize('python_venv_name', CUSTOM_VENVS_NAMES)
class Test_Ansible_Tower_Modules(APITest):
    def run_tower_module(self, module_name, module_args, factories, is_docker, v2, request, ansible_collections_path, virtual_env_path=None, more_vars=None):
        if is_docker:
            jobs_settings = v2.settings.get().get_endpoint('jobs')
            prev_proot_show_paths = jobs_settings.AWX_PROOT_SHOW_PATHS
            jobs_settings.AWX_PROOT_SHOW_PATHS = prev_proot_show_paths + [ansible_collections_path]
            request.addfinalizer(lambda: jobs_settings.patch(AWX_PROOT_SHOW_PATHS=prev_proot_show_paths))

        module_name = 'awx.awx.' + module_name
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

    def test_ansible_tower_fully_qualified_collection_name(self, factories, venv_path, python_venv_name, ansible_collections_path, request, update_setting_pg, v2, is_docker):
        org = factories.organization()
        # TODO: update module name to "awx.awx.tower_organization" when modules are fully migrated
        # or maybe "awx.awx.organization", still not fully decided
        # no assertion here because only testing that job was successful
        # also test "ansible.tower.xxx"
        self.run_tower_module(
            'tower_organization', {'name': org.name},
            factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name)
        )

    def test_ansible_tower_module_organization_create_update(self, factories, venv_path, python_venv_name, ansible_collections_path, request, update_setting_pg, v2, is_docker):
        org_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.organizations.get(name=org_name).results[0].delete())
        self.run_tower_module('tower_organization', {
            'name': org_name,
            'description': 'hello world',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        org = v2.organizations.get(name=org_name).results.pop()
        org_id = org.id
        assert org_name == org['name']
        assert org['description'] == 'hello world'

        # Test updating the object
        self.run_tower_module('tower_organization', {
            'name': org_name,
            'description': 'updated description',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        org = v2.organizations.get(name=org_name).results.pop()
        assert org.id == org_id
        assert org_name == org['name']
        assert org['description'] == 'updated description'

    def test_ansible_tower_module_organization_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        org = factories.organization()
        self.run_tower_module('tower_organization', {
            'name': org.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.organizations.get(name=org.name).results)

    def test_ansible_tower_module_organization_check_mode(self, factories, tower_version, venv_path, python_venv_name, is_docker, v2, request, ansible_collections_path):
        '''
        Ensure that orgnization check_mode: True returns the tower_version
        '''
        org = factories.organization()
        job = self.run_tower_module(
            'tower_organization', {'name': org.name}, factories,
            is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name),
            more_vars={'check_mode': True}
        )

        job_event = job.get_related('job_events').get(event='runner_on_ok', task='invoke_arbitrary_module').results[0]
        module_tower_version = job_event['event_data']['res']['tower_version']

        assert tower_version == module_tower_version

    def test_ansible_tower_module_project_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, organization, is_docker):
        proj_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.projects.get(name=proj_name).results[0].delete())
        self.run_tower_module('tower_project', {
            'name': proj_name,
            'description': 'hello world',
            'scm_type': 'git',
            'scm_url': 'git@github.com:ansible/test-playbooks.git',
            'organization': organization.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        proj = v2.projects.get(name=proj_name).results[0]
        proj_id = proj.id
        proj.related.project_updates.get().results[0].wait_until_completed()
        assert proj_name == proj['name']
        assert proj['description'] == 'hello world'
        assert proj['scm_type'] == 'git'
        assert proj['scm_url'] == 'git@github.com:ansible/test-playbooks.git'
        assert proj['organization'] == organization.id

        self.run_tower_module('tower_project', {
            'name': proj_name,
            'description': 'updated description',
            'scm_type': 'git',
            'scm_url': 'git@github.com:ansible/test-playbooks.git',
            'organization': organization.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        proj = v2.projects.get(name=proj_name).results[0]
        proj.related.project_updates.get().results[0].wait_until_completed()
        assert proj.id == proj_id
        assert proj_name == proj['name']
        assert proj['description'] == 'updated description'
        assert proj['scm_type'] == 'git'
        assert proj['scm_url'] == 'git@github.com:ansible/test-playbooks.git'
        assert proj['organization'] == organization.id

    def test_ansible_tower_module_project_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        proj = factories.project()
        self.run_tower_module('tower_project', {
            'name': proj.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert not v2.projects.get(name=proj.name).results

    def test_ansible_tower_module_credential_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, organization, is_docker):
        cred_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.credentials.get(name=cred_name).results[0].delete())
        self.run_tower_module('tower_credential', {
            'name': cred_name,
            'description': 'hello world',
            'kind': 'ssh',
            'organization': organization.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        cred = v2.credentials.get(name=cred_name).results.pop()
        cred_id = cred.id
        assert cred_name == cred['name']
        assert cred['description'] == 'hello world'
        assert cred['kind'] == 'ssh'
        assert cred['organization'] == organization.id

        self.run_tower_module('tower_credential', {
            'name': cred_name,
            'description': 'updated description',
            'kind': 'ssh',
            'organization': organization.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        cred = v2.credentials.get(name=cred_name).results.pop()
        assert cred_id == cred.id
        assert cred_name == cred['name']
        assert cred['description'] == 'updated description'
        assert cred['kind'] == 'ssh'
        assert cred['organization'] == organization.id

    def test_ansible_tower_module_credential_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        cred = factories.credential()
        self.run_tower_module('tower_credential', {
            'name': cred.name,
            'state': 'absent',
            'kind': cred.kind,
            'organization': cred.summary_fields.organization.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.credentials.get(name=cred.name).results)

    def test_ansible_tower_module_credential_type_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, organization,
            is_docker):
        cred_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.credential_types.get(name=cred_name).results[0].delete())
        self.run_tower_module('tower_credential_type', {
            'name': cred_name,
            'description': 'hello world',
            'kind': 'cloud',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        cred = v2.credential_types.get(name=cred_name).results.pop()
        cred_id = cred.id
        assert cred_name == cred['name']
        assert cred['description'] == 'hello world'
        assert cred['kind'] == 'cloud'

        self.run_tower_module('tower_credential_type', {
            'name': cred_name,
            'description': 'updated description',
            'kind': 'cloud',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        cred = v2.credential_types.get(name=cred_name).results.pop()
        assert cred.id == cred_id
        assert cred_name == cred['name']
        assert cred['description'] == 'updated description'
        assert cred['kind'] == 'cloud'

    def test_ansible_tower_module_credential_type_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        cred = factories.credential_type()
        self.run_tower_module('tower_credential_type', {
            'name': cred.name,
            'state': 'absent',
            'kind': cred.kind,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.credential_types.get(name=cred.name).results)

    def test_ansible_tower_module_notification_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, organization, is_docker):
        notification_name = utils.random_title()
        request.addfinalizer(lambda *args: v2.notification_templates.get(name=notification_name).results[0].delete())
        self.run_tower_module('tower_notification', {
            'name': notification_name,
            'organization': organization.name,
            'description': 'hello world',
            'channels': '[#foo]',
            'notification_type': 'slack',
            'token': 'fake_token',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        notification = v2.notification_templates.get(name=notification_name).results.pop()
        notification_id = notification.id
        assert notification_name == notification['name']
        assert notification['description'] == 'hello world'
        assert notification.summary_fields.organization.name == organization.name
        assert notification['notification_type'] == 'slack'

        self.run_tower_module('tower_notification', {
            'name': notification_name,
            'organization': organization.name,
            'description': 'updated description',
            'channels': '[#foo]',
            'notification_type': 'slack',
            'token': 'fake_token',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        notification = v2.notification_templates.get(name=notification_name).results.pop()
        assert notification.id == notification_id
        assert notification_name == notification['name']
        assert notification['description'] == 'updated description'
        assert notification.summary_fields.organization.name == organization.name
        assert notification['notification_type'] == 'slack'

    def test_ansible_tower_module_notification_delete(self, v2, factories, venv_path, python_venv_name, organization, is_docker, request, ansible_collections_path):
        token = utils.random_title()
        notification = factories.notification_template(token=token)
        self.run_tower_module('tower_notification', {
            'name': notification.name,
            'organization': notification.summary_fields.organization.name,
            'channels': str(notification.notification_configuration.channels),
            'notification_type': notification.notification_type,
            'token': token,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        notifications = v2.notification_templates.get(name=notification.name).results
        assert not notifications

    def test_ansible_tower_module_group_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        group_name = utils.random_title()
        inv = factories.inventory()
        request.addfinalizer(lambda *args: v2.groups.get(name=group_name).results[0].delete())
        self.run_tower_module('tower_group', {
            'name': group_name,
            'description': 'hello world',
            'inventory': inv.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        group = v2.groups.get(name=group_name).results.pop()
        group_id = group.id
        assert group_name == group['name']
        assert group['description'] == 'hello world'
        assert group['inventory'] == inv.id

        self.run_tower_module('tower_group', {
            'name': group_name,
            'description': 'updated description',
            'inventory': inv.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        group = v2.groups.get(name=group_name).results.pop()
        assert group.id == group_id
        assert group_name == group['name']
        assert group['description'] == 'updated description'
        assert group['inventory'] == inv.id

    def test_ansible_tower_module_group_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        group = factories.group()
        self.run_tower_module('tower_group', {
            'name': group.name,
            'inventory': group.summary_fields.inventory.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.groups.get(name=group.name).results)

    def test_ansible_tower_module_host_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        host_name = utils.random_title()
        inv = factories.inventory()
        request.addfinalizer(lambda *args: v2.hosts.get(name=host_name).results[0].delete())
        self.run_tower_module('tower_host', {
            'name': host_name,
            'description': 'hello world',
            'inventory': inv.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        host = v2.hosts.get(name=host_name).results.pop()
        host_id = host.id
        assert host_name == host['name']
        assert host['description'] == 'hello world'
        assert host['inventory'] == inv.id

        self.run_tower_module('tower_host', {
            'name': host_name,
            'description': 'updated description',
            'inventory': inv.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        host = v2.hosts.get(name=host_name).results.pop()
        assert host.id == host_id
        assert host_name == host['name']
        assert host['description'] == 'updated description'
        assert host['inventory'] == inv.id

    def test_ansible_tower_module_host_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        host = factories.host()
        self.run_tower_module('tower_host', {
            'name': host.name,
            'inventory': host.summary_fields.inventory.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.hosts.get(name=host.name).results)

    def test_ansible_tower_module_inventory_create_update(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        inventory_name = utils.random_title()
        org = factories.organization()
        request.addfinalizer(lambda *args: v2.inventory.get(name=inventory_name).results[0].delete())
        self.run_tower_module('tower_inventory', {
            'name': inventory_name,
            'description': 'hello world',
            'organization': org.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        inventory = v2.inventory.get(name=inventory_name).results.pop()
        inventory_id = inventory.id
        assert inventory_name == inventory['name']
        assert inventory['description'] == 'hello world'
        assert inventory['organization'] == org.id

        self.run_tower_module('tower_inventory', {
            'name': inventory_name,
            'description': 'updated description',
            'organization': org.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        inventory = v2.inventory.get(name=inventory_name).results.pop()
        assert inventory_id == inventory.id
        assert inventory_name == inventory['name']
        assert inventory['description'] == 'updated description'
        assert inventory['organization'] == org.id

    def test_ansible_tower_module_inventory_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        inventory = factories.inventory()
        self.run_tower_module('tower_inventory', {
            'name': inventory.name,
            'organization': inventory.summary_fields.organization.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.inventory.get(name=inventory.name).results)

    def test_ansible_tower_module_inventory_source_create_update(self, request, ansible_collections_path, factories, v2, venv_path, python_venv_name, is_docker):
        inventory_source_name = utils.random_title()
        org = factories.organization()
        inventory_script = factories.inventory_script(organization=org)
        inventory = factories.inventory(organization=org)
        request.addfinalizer(lambda *args: v2.inventory_sources.get(name=inventory_source_name).results[0].delete())
        self.run_tower_module('tower_inventory_source', {
            'name': inventory_source_name,
            'inventory': inventory.name,
            'description': 'hello world',
            'source': 'custom',
            'source_script': inventory_script.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        inventory_source = v2.inventory_sources.get(name=inventory_source_name).results.pop()
        inventory_source_id = inventory_source.id
        assert inventory_source_name == inventory_source['name']
        assert inventory_source['description'] == 'hello world'

        self.run_tower_module('tower_inventory_source', {
            'name': inventory_source_name,
            'inventory': inventory.name,
            'description': 'updated description',
            'source': 'custom',
            'source_script': inventory_script.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        inventory_source = v2.inventory_sources.get(name=inventory_source_name).results.pop()
        assert inventory_source_id == inventory_source.id
        assert inventory_source_name == inventory_source['name']
        assert inventory_source['description'] == 'updated description'

    def test_ansible_tower_module_inventory_source_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        inventory_source = factories.inventory_source()
        self.run_tower_module('tower_inventory_source', {
            'name': inventory_source.name,
            'inventory': inventory_source.summary_fields.inventory.name,
            'source': inventory_source.source,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert 0 == len(v2.inventory_sources.get(name=inventory_source.name).results)

    def test_ansible_tower_module_job(self, request, ansible_collections_path, factories, v2, venv_path, python_venv_name, is_docker):
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

        # Create a JT
        request.addfinalizer(cleanup_jt)
        self.run_tower_module('tower_job_template', {
            'name': jt_name,
            'description': 'hello world',
            'job_type': 'run',
            'inventory': inventory.name,
            'playbook': 'sleep.yml',
            'project': project.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        jt = v2.job_templates.get(name=jt_name).results.pop()
        jt_id = jt.id
        assert jt_name == jt['name']
        assert jt['description'] == 'hello world'
        assert jt['job_type'] == 'run'
        assert jt['inventory'] == inventory.id
        assert jt['playbook'] == 'sleep.yml'
        assert jt['project'] == project.id

        # Update the JT
        self.run_tower_module('tower_job_template', {
            'name': jt_name,
            'description': 'updated description',
            'job_type': 'run',
            'inventory': inventory.name,
            'playbook': 'sleep.yml',
            'project': project.name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        jt = v2.job_templates.get(name=jt_name).results.pop()
        assert jt.id == jt_id
        assert jt_name == jt['name']
        assert jt['description'] == 'updated description'
        assert jt['job_type'] == 'run'
        assert jt['inventory'] == inventory.id
        assert jt['playbook'] == 'sleep.yml'
        assert jt['project'] == project.id

        # Launch the JT we just built
        self.run_tower_module('tower_job_launch', {
            'job_template': jt_name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        job = v2.jobs.get(name=jt_name).results.pop()
        assert job.summary_fields.job_template.name == jt_name

        job_id1 = job.id

        # Cancel the job we just launched
        self.run_tower_module('tower_job_cancel', {
            'job_id': job_id1,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        job = v2.jobs.get(id=job_id1).results.pop()
        assert job.summary_fields.job_template.name == jt_name
        job.assert_status("canceled")

        # Launch another job
        self.run_tower_module('tower_job_launch', {
            'job_template': jt_name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        job = v2.jobs.get(name=jt_name).results[1]
        assert job.summary_fields.job_template.name == jt_name

        job_id2 = job.id

        # Sanity check
        assert job_id1 != job_id2

        # Wait for the job we just launched
        self.run_tower_module('tower_job_wait', {
            'job_id': job_id2,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        job = v2.jobs.get(id=job_id2).results.pop()
        assert job.summary_fields.job_template.name == jt_name
        job.assert_status("successful")

        # List jobs
        # I'm not entirely sure how to test this better
        job_output = self.run_tower_module('tower_job_list', {}, factories,
                is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name)).wait_until_completed()

        # Basic test
        job_output.assert_status('successful')

        # Remove our job template
        self.run_tower_module('tower_job_template', {
            'name': jt_name,
            'job_type': 'run',
            'inventory': inventory.name,
            'playbook': 'sleep.yml',
            'project': project.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        job_templates = v2.job_templates.get(name=jt_name).results
        assert not job_templates

    def test_ansible_tower_module_role_create(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        org = factories.organization()
        user = factories.user()
        self.run_tower_module('tower_role', {
            'user': user.username,
            'organization': org.name,
            'role': 'admin',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        role = v2.users.get(id=user.id)['results'][0]['related']['roles'].get().results.pop()
        assert str(org.id) in role['related']['organization']
        assert role['related']['users'].get()['results'][0]['id'] == user.id

    def test_ansible_tower_module_team_create(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        team_name = utils.random_title()
        org = factories.organization()
        request.addfinalizer(lambda *args: v2.teams.get(name=team_name).results[0].delete())
        self.run_tower_module('tower_team', {
            'name': team_name,
            'organization': org.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        team = v2.teams.get(name=team_name).results.pop()
        assert team_name == team['name']
        assert team['organization'] == org.id

    def test_ansible_tower_module_team_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        team = factories.team()
        self.run_tower_module('tower_team', {
            'name': team.name,
            'organization': team.summary_fields.organization.name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert not v2.teams.get(name=team.name).results

    def test_ansible_tower_module_user_create(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        username = utils.random_title(non_ascii=False)
        request.addfinalizer(lambda *args: v2.users.get(username=username).results[0].delete())
        self.run_tower_module('tower_user', {
            'username': username,
            'password': username,
            'email': 'example@example.com',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        user = v2.users.get(username=username).results.pop()
        assert username == user['username']
        assert user['email'] == 'example@example.com'

    def test_ansible_tower_module_user_delete(self, factories, v2, venv_path, python_venv_name, is_docker, request, ansible_collections_path):
        user = factories.user()
        self.run_tower_module('tower_user', {
            'username': user.username,
            'email': user.email,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        assert not v2.users.get(username=user.username).results

    def test_ansible_tower_module_label_create(self, request, ansible_collections_path, v2, factories, venv_path, python_venv_name, is_docker):
        label_name = utils.random_title()
        org = factories.organization()
        self.run_tower_module('tower_label', {
            'name': label_name,
            'organization': org.name
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        label = v2.labels.get(name=label_name).results.pop()
        assert label_name == label['name']

    def test_ansible_tower_module_workflow(self, request, ansible_collections_path, factories, v2, venv_path, python_venv_name, is_docker):
        wf_name = utils.random_title()

        # We need this to teardown the WF if it fails before the end. The try
        # block also means it wont fail if we get to the end and clean up the
        # WF as part of the test
        def cleanup_wf():
            try:
                return v2.workflow_job_templates.get(name=wf_name).results[0].delete()
            except:
                print("failed to remove WF in teardown")

        request.addfinalizer(cleanup_wf)
        self.run_tower_module('tower_workflow_template', {
            'name': wf_name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        wf = v2.workflow_job_templates.get(name=wf_name).results.pop()
        assert wf_name == wf['name']

        # launch our workflow
        self.run_tower_module('tower_workflow_launch', {
            'workflow_template': wf_name,
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        wf_job = v2.workflow_jobs.get(name=wf_name).results.pop()
        assert wf_job['status'] == 'successful'
        assert wf_name == wf_job['name']

        # Remove our workflow
        self.run_tower_module('tower_workflow_template', {
            'name': wf_name,
            'state': 'absent',
        }, factories, is_docker, v2, request, ansible_collections_path, venv_path(python_venv_name))

        workflow_templates = v2.workflow_job_templates.get(name=wf_name).results
        assert not workflow_templates
