import dateutil.rrule
import logging
import os.path
import json

from towerkit.rrule import RRule
import fauxfactory
import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def project_ansible_helloworld_hg(factories, organization):
    project = factories.project(scm_type='hg', scm_url='https://bitbucket.org/jlaska/ansible-helloworld',
                                organization=organization)
    return project


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
def project_ansible_playbooks_manual(request, factories, ansible_runner, api_config_pg, organization):
    local_path = 'project_dir_{0}'.format(fauxfactory.gen_alphanumeric())
    base_dir = api_config_pg.project_base_dir
    full_path = os.path.join(base_dir, local_path)
    contacted = ansible_runner.git(repo='https://github.com/ansible/test-playbooks.git', dest=full_path)
    result = contacted.values()[0]
    assert not result.get('failed'), "Clone failed\n{0}".format(json.dumps(result, indent=4))

    project = factories.project(name="ansible-playbooks.manual - {0}".format(local_path),
                                local_path=local_path, scm_type='', wait=False, organization=organization)

    def delete_local_project():
        ansible_runner.file(state="absent", path=full_path)

    request.addfinalizer(delete_local_project)
    return project


@pytest.fixture(scope="function")
def project_ansible_git_nowait(factories, organization):
    project = factories.project(name="ansible.git - {0}".format(fauxfactory.gen_alphanumeric()),
                                scm_type='git', scm_url='https://github.com/ansible/ansible.git',
                                organization=organization, wait=False)
    return project


@pytest.fixture(scope="function")
def project_ansible_git(project_ansible_git_nowait):
    updates = project_ansible_git_nowait.related.project_updates.get(order_by="-id")
    assert updates.count > 0, 'No project updates found'
    assert updates.results.pop().wait_until_completed().is_successful
    return project_ansible_git_nowait.get()


@pytest.fixture(scope="function")
def project_ansible_docsite_git_nowait(factories, encrypted_scm_credential, organization):
    project = factories.project(name="ansible-docsite.git - {0}".format(fauxfactory.gen_alphanumeric()),
                                scm_type='git', scm_url='git@github.com:ansible/docsite.git',
                                credential=encrypted_scm_credential, organization=organization)
    return project


@pytest.fixture(scope="function")
def project_ansible_docsite_git(project_ansible_docsite_git_nowait):
    updates = project_ansible_docsite_git_nowait.related.project_updates.get(order_by="-id")
    assert updates.count > 0, 'No project updates found'
    assert updates.results.pop().wait_until_completed().is_successful
    return project_ansible_docsite_git_nowait.get()


@pytest.fixture(scope="function")
def project_with_schedule(project_ansible_playbooks_git):
    rrule = RRule(dateutil.rrule.DAILY, count=1, byminute='', bysecond='', byhour='')
    project_ansible_playbooks_git.add_schedule(rrule=rrule)
    return project_ansible_playbooks_git.get()
