import pytest
import common.utils

# from credentials import ssh_credential
# from projects import project
# from inventories import inventory


@pytest.fixture(scope="function")
def job_template_no_credential(request, authtoken, api_job_templates_pg, project, inventory):
    '''Define a job_template with no machine credential'''

    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template without credentials - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_with_limit(request, authtoken, api_job_templates_pg, project, inventory, ssh_credential):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with limit - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project.id,
                   limit='No_Match',
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_ask(request, authtoken, api_job_templates_pg, project, inventory, ssh_credential_ask):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with ASK credential - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential_ask.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template(request, authtoken, api_job_templates_pg, project, inventory, ssh_credential):
    '''Define a job_template with a valid machine credential'''

    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with machine credentials - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj
