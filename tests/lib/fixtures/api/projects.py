import pytest
import common.utils

# from organizations import organization
# from credentials import scm_credential_key_unlock_ASK

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
    updates_pg = obj.get_related('project_updates', order_by="-id")
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop().wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, \
        "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s\nJob explanation: %s" % \
        (latest_update_pg.status, latest_update_pg.result_stdout, latest_update_pg.result_traceback, latest_update_pg.job_explanation)

    return obj

@pytest.fixture(scope="function")
def project_ansible_playbooks_git(request, authtoken, api_projects_pg, organization):
    # Create project
    payload = dict(name="ansible-playbooks.git - %s" % common.utils.random_unicode(),
                   organization=organization.id,
                   scm_type='git',
                   scm_url='https://github.com/jlaska/ansible-playbooks.git',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)
    obj = api_projects_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Wait for project update to complete
    updates_pg = obj.get_related('project_updates', order_by="-id")
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop().wait_until_completed()
    # Assert project_update completed successfully
    assert latest_update_pg.is_successful, \
        "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s\nJob explanation: %s" % \
        (latest_update_pg.status, latest_update_pg.result_stdout, latest_update_pg.result_traceback, latest_update_pg.job_explanation)

    return obj

@pytest.fixture(scope="function")
def project(request, authtoken, api_projects_pg, organization):
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

    return obj


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
