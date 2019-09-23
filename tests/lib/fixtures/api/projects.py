import dateutil.rrule
import logging
import os.path
import json

from tests.lib.rrule import RRule
from awxkit.utils import random_title
from awxkit.config import config

import fauxfactory
import pytest


log = logging.getLogger(__name__)


@pytest.fixture
def git_file_path(skip_if_cluster, request, ansible_adhoc, is_docker):
    """Makes a git repo on the file system"""
    if is_docker:
        root = '/awx_devel'
    else:
        root = '/home'
    path = '{}/at_{}_test/'.format(root, random_title(non_ascii=False))
    ansible_module = ansible_adhoc().tower
    if not config.prevent_teardown:
        request.addfinalizer(lambda: ansible_module.file(path=path, state='absent'))
    sync = ansible_module.git(repo='git://github.com/ansible/test-playbooks.git', dest=path)
    assert len(sync), 'No hosts in tower group to target'
    for result in sync.values():
        assert result.get('after'), result
    return 'file://{0}'.format(path)


@pytest.fixture
def source_change_add_and_remove(git_file_path, ansible_adhoc):
    def rf():
        '''This fixture makes commits to the master branch of the repo on the
        Tower server at the location given by git_file_path
        '''
        ansible_module = ansible_adhoc().tower
        local_path = git_file_path[len('file://'):]
        tmp_filename = random_title(non_ascii=False)
        ansible_module.file(path=os.path.join(local_path, tmp_filename), state='touch')
        run_these = [
            'git config user.email arominge@redhat.com',
            'git config user.name DoneByTest',
            'git add {}'.format(tmp_filename),
            'git commit -m "Adding temporary file {}"'.format(tmp_filename),
            'git rm {}'.format(tmp_filename),
            'git commit -m "Removing temporary file {}"'.format(tmp_filename)
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)

            for result in contacted.values():
                assert 'rc' in result, result
                assert result['rc'] == 0, result
        return tmp_filename
    return rf


@pytest.fixture(scope="function")
def project_ansible_playbooks_git_nowait(factories, organization):
    project = factories.project(scm_type='git', scm_url='https://github.com/ansible/test-playbooks.git',
                                organization=organization, wait=False)
    return project


@pytest.fixture(scope="function")
def project_ansible_playbooks_git(project_ansible_playbooks_git_nowait):
    updates = project_ansible_playbooks_git_nowait.related.project_updates.get(order_by="-id")
    assert updates.count > 0, 'No project updates found'
    assert updates.results.pop().wait_until_completed().is_successful
    return project_ansible_playbooks_git_nowait.get()


@pytest.fixture(scope="function")
def project(project_ansible_playbooks_git):
    return project_ansible_playbooks_git


@pytest.fixture(scope="function")
def project_update_with_status_completed(project_ansible_playbooks_git):
    return project_ansible_playbooks_git.related.last_update.get()


@pytest.fixture(scope="function")
def project_ansible_playbooks_manual(request, factories, ansible_adhoc, api_config_pg, organization):
    local_path = 'project_dir_{0}'.format(fauxfactory.gen_alphanumeric())
    base_dir = api_config_pg.project_base_dir
    full_path = os.path.join(base_dir, local_path)
    ansible_module = ansible_adhoc().tower  # set up on _all_ tower nodes
    contacted = ansible_module.git(repo='https://github.com/ansible/test-playbooks.git', dest=full_path)
    for host, result in contacted.items():
        assert not result.get('failed'), "Clone on host {0} failed\n{1}".format(host, json.dumps(result, indent=4))

    project = factories.project(name="ansible-playbooks.manual - {0}".format(local_path),
                                local_path=local_path, scm_type='', wait=False, organization=organization)

    def delete_local_project():
        ansible_module.file(state="absent", path=full_path)

    request.addfinalizer(delete_local_project)
    return project


@pytest.fixture(scope="function")
def project_ansible_git_nowait(factories, organization, ansible_version):
    scm_branch = 'devel' if 'dev' in ansible_version else 'stable-%s' % ansible_version[0:3]
    project = factories.project(name="ansible.git - {0}".format(fauxfactory.gen_alphanumeric()),
                                scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                scm_branch=scm_branch, organization=organization, wait=False)
    return project


@pytest.fixture(scope="function")
def project_ansible_git(project_ansible_git_nowait):
    updates = project_ansible_git_nowait.related.project_updates.get(order_by="-id")
    assert updates.count > 0, 'No project updates found'
    assert updates.results.pop().wait_until_completed().is_successful
    return project_ansible_git_nowait.get()


@pytest.fixture(scope="function")
def project_ansible_docsite_git(factories, encrypted_scm_credential, organization):
    project = factories.project(name="ansible-docsite.git - {0}".format(fauxfactory.gen_alphanumeric()),
                                scm_type='git', scm_url='git@github.com:ansible/docsite.git',
                                credential=encrypted_scm_credential, organization=organization)
    assert project.status == 'successful'
    return project


@pytest.fixture(scope="function")
def project_with_schedule(project_ansible_playbooks_git):
    rrule = RRule(dateutil.rrule.DAILY, count=1, byminute='', bysecond='', byhour='')
    project_ansible_playbooks_git.add_schedule(rrule=rrule)
    return project_ansible_playbooks_git.get()
