import json
import os.path
import pytest
import common.utils


@pytest.fixture(scope="function")
def project_scm_type_choices(request, authtoken, api_projects_pg):
    '''Return project scm_types from OPTIONS'''
    return dict(api_projects_pg.options().json['actions']['GET']['scm_type']['choices'])


@pytest.fixture(scope="function")
def project_status_choices(request, authtoken, api_projects_pg):
    '''Return project statuses from OPTIONS'''
    return dict(api_projects_pg.options().json['actions']['GET']['status']['choices'])


@pytest.fixture(scope="function")
def project_ansible_helloworld_hg(request, authtoken, api_projects_pg, organization):
    # Create project
    payload = dict(name="project-%s" % common.utils.random_unicode(),
                   organization=organization.id,
                   scm_type='hg',
                   scm_url='https://bitbucket.org/jlaska/ansible-helloworld',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)

    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Wait for project update to complete
    latest_update_pg = obj.get_related('current_update').wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg
    return obj.get()


@pytest.fixture(scope="function")
def project(request, project_ansible_helloworld_hg):
    return project_ansible_helloworld_hg


@pytest.fixture(scope="function")
def project_ansible_playbooks_manual(request, authtoken, ansible_runner, awx_config, api_projects_pg, organization):
    '''
    Create a manual project associated with ansible-playbooks.git
    '''
    local_path = common.utils.random_ascii()

    # Clone the repo
    results = ansible_runner.git(repo='https://github.com/jlaska/ansible-playbooks.git',
                                 dest=os.path.join(awx_config['project_base_dir'], local_path))
    assert 'failed' not in results, "Clone failed\n%s" % json.dumps(results, indent=4)

    # Create project
    payload = dict(name="ansible-playbooks.git - %s" % local_path,
                   organization=organization.id,
                   local_path=local_path,
                   scm_type=None)
    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.quiet_delete)
    return obj


@pytest.fixture(scope="function")
def project_manual(request, project_ansible_playbooks_manual):
    return project_ansible_playbooks_manual


@pytest.fixture(scope="function")
def project_ansible_playbooks_git_nowait(request, authtoken, api_projects_pg, organization):
    # Create project
    payload = dict(name="ansible-playbooks.git - %s" % common.utils.random_unicode(),
                   organization=organization.id,
                   scm_type='git',
                   scm_url='https://github.com/jlaska/ansible-playbooks.git',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)
    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.quiet_delete)
    return obj


@pytest.fixture(scope="function")
def project_ansible_playbooks_git(request, project_ansible_playbooks_git_nowait):
    # Wait for project update to complete
    updates_pg = project_ansible_playbooks_git_nowait.get_related('project_updates', order_by="-id")
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop().wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg
    return project_ansible_playbooks_git_nowait.get()


@pytest.fixture(scope="function")
def project_with_credential_prompt(request, authtoken, api_projects_pg, organization, scm_credential_key_unlock_ASK):
    # Create project
    payload = dict(name="project-%s" % common.utils.random_unicode(),
                   organization=organization.id,
                   scm_type='git',
                   scm_url='git@github.com:ansible/ansible-examples.git',
                   scm_key_unlock='ASK',
                   credential=scm_credential_key_unlock_ASK.id,)
    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def many_git_projects(request, authtoken, api_projects_pg, organization):
    obj_list = list()
    for i in range(55):
        payload = dict(name="project-%d-%s" % (i, common.utils.random_unicode()),
                       description="random project %d - %s" % (i, common.utils.random_unicode()),
                       organization=organization.id,
                       scm_type='git',
                       scm_url='https://github.com/jlaska/ansible-playbooks.git',
                       scm_clean=False,
                       scm_delete_on_update=False,
                       scm_update_on_launch=False,)
        obj = api_projects_pg.post(payload)
        request.addfinalizer(obj.quiet_delete)
        obj_list.append(obj)
    return obj_list


@pytest.fixture(scope="function")
def many_manual_projects(request, authtoken, ansible_runner, awx_config, api_projects_pg, organization):
    obj_list = list()
    for i in range(55):
        local_path = common.utils.random_ascii()
        ansible_runner.file(path=local_path, state='directory', owner='awx', group='awx', mode=0755)
        payload = dict(name="project-%d-%s" % (i, local_path),
                       description="random project %d - %s" % (i, common.utils.random_unicode()),
                       organization=organization.id,
                       scm_type=None,
                       local_path=local_path)
        obj = api_projects_pg.post(payload)
        request.addfinalizer(obj.quiet_delete)
        obj_list.append(obj)
    return obj_list
