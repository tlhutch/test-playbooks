import json
import os.path
import pytest
import logging
import fauxfactory
import common.exceptions


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def project_scm_type_choices(request, authtoken, api_projects_pg):
    '''Return project scm_types from OPTIONS'''
    return dict(api_projects_pg.options().json['actions']['GET']['scm_type']['choices'])


@pytest.fixture(scope="function")
def project_status_choices(request, authtoken, api_projects_pg):
    '''Return project statuses from OPTIONS'''
    return dict(api_projects_pg.options().json['actions']['GET']['status']['choices'])


@pytest.fixture(scope="function")
def project_ansible_helloworld_hg(request, authtoken, organization):
    # Create project
    payload = dict(name="project-%s" % fauxfactory.gen_utf8(),
                   scm_type='hg',
                   scm_url='https://bitbucket.org/jlaska/ansible-helloworld',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)

    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.delete)

    # Wait for project update to complete
    latest_update_pg = obj.get_related('current_update').wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg
    return obj.get()


@pytest.fixture(scope="function")
def project(request, project_ansible_playbooks_git):
    return project_ansible_playbooks_git


@pytest.fixture(scope="function")
def project_update_with_status_completed(request, project_ansible_playbooks_git):
    return project_ansible_playbooks_git.get_related('last_update')


@pytest.fixture(scope="function")
def project_ansible_playbooks_manual(request, authtoken, ansible_runner, awx_config, organization):
    '''
    Create a manual project associated with ansible-playbooks.git
    '''

    # Override the local_path

    fixture_args = getattr(request.function, 'fixture_args', None)
    if fixture_args and fixture_args.kwargs.get('local_path', False):
        local_path = fixture_args.kwargs['local_path']
    else:
        local_path = "project_dir_%s" % fauxfactory.gen_utf8()

    # Clone the repo
    results = ansible_runner.git(repo='https://github.com/jlaska/ansible-playbooks.git',
                                 dest=os.path.join(awx_config['project_base_dir'], local_path))
    assert 'failed' not in results, "Clone failed\n%s" % json.dumps(results, indent=4)

    # Initialize the project payload
    payload = dict(name="ansible-playbooks.manual - %s" % local_path,
                   description="manual project - %s" % fauxfactory.gen_utf8(),
                   local_path=local_path,
                   scm_type='')

    # customize the payload using fixture_args (optional)
    if fixture_args:
        payload.update(fixture_args.kwargs)

    try:
        obj = organization.get_related('projects').post(payload)
    except common.exceptions.Duplicate_Exception:
        log.debug("POST failed - %s" % json.dumps(payload, indent=2))
        raise

    request.addfinalizer(obj.silent_delete)

    # manually delete the local_path
    def delete_project():
        ansible_runner.file(state="absent",
                            path=os.path.join(awx_config['project_base_dir'], local_path))
    request.addfinalizer(delete_project)
    return obj


@pytest.fixture(scope="function")
def project_manual(request, project_ansible_playbooks_manual):
    return project_ansible_playbooks_manual


@pytest.fixture(scope="function")
def project_ansible_playbooks_git_nowait(request, authtoken, organization):
    # Create project
    payload = dict(name="ansible-playbooks.git - %s" % fauxfactory.gen_utf8(),
                   scm_type='git',
                   scm_url='https://github.com/jlaska/ansible-playbooks.git',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)
    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.silent_delete)
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
def project_ansible_git_nowait(request, authtoken, organization):
    # Create project
    payload = dict(name="ansible-playbooks.git - %s" % fauxfactory.gen_utf8(),
                   scm_type='git',
                   scm_url='https://github.com/ansible/ansible.git',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)
    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def project_ansible_git(request, project_ansible_git_nowait):
    # Wait for project update to complete
    updates_pg = project_ansible_git_nowait.get_related('project_updates', order_by="-id")
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop().wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg
    return project_ansible_git_nowait.get()


@pytest.fixture(scope="function")
def project_ansible_internal_git_nowait(request, authtoken, encrypted_scm_credential, organization):
    # Create project
    payload = dict(name="ansible-internal.git - %s" % fauxfactory.gen_utf8(),
                   scm_type='git',
                   scm_url='git@github.com:ansible/ansible-internal.git',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,
                   credential=encrypted_scm_credential.id)
    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def project_ansible_internal_git(request, project_ansible_internal_git_nowait):
    # Wait for project update to complete
    updates_pg = project_ansible_internal_git_nowait.get_related('project_updates', order_by="-id")
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop().wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg
    return project_ansible_internal_git_nowait.get()


@pytest.fixture(scope="function")
def project_with_credential_prompt(request, authtoken, organization, scm_credential_key_unlock_ASK):
    # Create project
    payload = dict(name="project-%s" % fauxfactory.gen_utf8(),
                   scm_type='git',
                   scm_url='git@github.com:ansible/ansible-examples.git',
                   scm_key_unlock='ASK',
                   credential=scm_credential_key_unlock_ASK.id,)
    obj = organization.get_related('projects').post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def many_git_projects(request, authtoken, organization):
    obj_list = list()
    related = organization.get_related('projects')
    for i in range(55):
        payload = dict(name="project-%d-%s" % (i, fauxfactory.gen_utf8()),
                       description="random project %d - %s" % (i, fauxfactory.gen_utf8()),
                       scm_type='git',
                       scm_url='https://github.com/jlaska/ansible-playbooks.git',
                       scm_clean=False,
                       scm_delete_on_update=False,
                       scm_update_on_launch=False,)
        obj = related.post(payload)
        request.addfinalizer(obj.silent_delete)
        obj_list.append(obj)
    return obj_list


@pytest.fixture(scope="function")
def many_manual_projects(request, authtoken, ansible_runner, awx_config, organization):
    obj_list = list()
    related = organization.get_related('projects')
    for i in range(55):
        # create project path
        local_path = "project_dir_%s" % fauxfactory.gen_utf8()
        ansible_runner.file(path=os.path.join(awx_config['project_base_dir'], local_path),
                            state='directory', owner='awx', group='awx', mode=0755)
        # create manual project
        payload = dict(name="project-%d-%s" % (i, local_path),
                       description="random project %d - %s" % (i, fauxfactory.gen_utf8()),
                       scm_type=None,
                       local_path=local_path)
        obj = related.post(payload)
        obj_list.append(obj)
        request.addfinalizer(obj.silent_delete)

        # delete project directory when finished
        def delete_project_dir():
            return ansible_runner.file(state='absent', path=os.path.join(awx_config['project_base_dir'], local_path))
        request.addfinalizer(delete_project_dir)
    return obj_list
