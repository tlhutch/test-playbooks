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
def job_template_multi_ask(request, authtoken, api_job_templates_pg, project, inventory, ssh_credential_multi_ask):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with multiple ASK credential - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential_multi_ask.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_ansible_playbooks_git(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, inventory, ssh_credential):
    '''Define a job_template with a valid machine credential'''

    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template using ansible-playbooks.git - %s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
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


@pytest.fixture(scope="function")
def job_template_sleep(job_template_ansible_playbooks_git, host_local):
    return job_template_ansible_playbooks_git.patch(playbook='sleep.yml')


@pytest.fixture(scope="function")
def job_template_ping(job_template_ansible_playbooks_git, host_local):
    return job_template_ansible_playbooks_git.patch(playbook='ping.yml')


@pytest.fixture(scope="function")
def api_job_templates_options_json(authtoken, api_job_templates_pg):
    '''Return job_template OPTIONS json'''
    return api_job_templates_pg.options().json


@pytest.fixture(scope="function")
def job_template_status_choices(api_job_templates_options_json):
    '''Return job_template statuses from OPTIONS'''
    return dict(api_job_templates_options_json['actions']['GET']['status']['choices'])


# @pytest.fixture(scope="function")
# def job_template_no_credential(job_template_ping):
#     return job_template_ping.patch(credential=None)


@pytest.fixture(scope="function")
def job_template_ask_variables_on_launch(job_template_ping):
    return job_template_ping.patch(ask_variables_on_launch=True)


@pytest.fixture(scope="function")
def optional_survey_spec():
    payload = dict(name=common.utils.random_unicode(),
                   description=common.utils.random_unicode(),
                   spec=[dict(required=False,
                              question_name="Enter your email &mdash; &euro;",
                              variable="submitter_email",
                              type="text",),
                         dict(required=False,
                              question_name="Enter your employee number email &mdash; &euro;",
                              variable="submitter_email",
                              type="integer",)])
    return payload


@pytest.fixture(scope="function")
def required_survey_spec():
    payload = dict(name=common.utils.random_unicode(),
                   description=common.utils.random_unicode(),
                   spec=[dict(required=True,
                              question_name="Do you like chicken?",
                              question_description="Please indicate your chicken preference:",
                              variable="likes_chicken",
                              type="multiselect",
                              choices="yes"),
                         dict(required=True,
                              question_name="Favorite color?",
                              question_description="Pick a color darnit!",
                              variable="favorite_color",
                              type="multiplechoice",
                              choices="red\ngreen\nblue",
                              default="green"),
                         dict(required=False,
                              question_name="Enter your email &mdash; &euro;",
                              variable="submitter_email",
                              type="text")])
    return payload


@pytest.fixture(scope="function")
def job_template_variables_needed_to_start(job_template_ping, required_survey_spec):
    obj = job_template_ping.patch(survey_enabled=True)
    obj.get_related('survey_spec').post(required_survey_spec)
    return obj


@pytest.fixture(scope="function")
def job_template_passwords_needed_to_start(job_template_ping, ssh_credential_multi_ask):
    return job_template_ping.patch(credential=ssh_credential_multi_ask.id)
