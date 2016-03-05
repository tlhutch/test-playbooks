import pytest
import json
import fauxfactory

# from credentials import ssh_credential
# from projects import project
# from inventories import inventory


@pytest.fixture(scope="function")
def job_template_no_credential(request, authtoken, api_job_templates_pg, project, host_local):
    '''Define a job_template with no machine credential'''

    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_with_random_limit(request, authtoken, api_job_templates_pg, project, host_local, ssh_credential):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template with limit - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   limit='Random limit - %s' % fauxfactory.gen_utf8(),
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_ask(request, authtoken, api_job_templates_pg, project, host_local, ssh_credential_ask):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template with ASK credential - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential_ask.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_multi_ask(request, authtoken, api_job_templates_pg, project, host_local, ssh_credential_multi_ask):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template with multiple ASK credential - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential_multi_ask.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def job_template_ansible_playbooks_git(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, host_local, ssh_credential):
    '''Define a job_template with a valid machine credential'''

    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template using ansible-playbooks.git - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def job_template(request, authtoken, api_job_templates_pg, project, host_local, ssh_credential):
    '''Define a job_template with a valid machine credential'''

    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template with machine credentials - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential.id,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def another_job_template(request, authtoken, api_job_templates_pg, job_template):
    '''Define a job_template with a valid machine credential'''

    payload = job_template.json
    payload.update(name="Another job template - %s" % fauxfactory.gen_utf8())
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.silent_delete)
    return obj


@pytest.fixture(scope="function")
def job_template_with_extra_vars(request, authtoken, api_job_templates_pg, project, ssh_credential, host_local):
    '''Define a job_template with a set of extra_vars'''

    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template with machine credential - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential.id,
                   playbook='site.yml',  # This depends on the project selected
                   extra_vars=json.dumps(dict(one=1, two=2, three=3, intersection="job template")))
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def check_job_template(job_template):
    return job_template.patch(job_type="check")


@pytest.fixture(scope="function")
def scan_job_template(request, authtoken, api_job_templates_pg, ssh_credential, host_local):
    '''Define a basic scan job_template'''

    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random scan job_template with machine credential - %s" % fauxfactory.gen_utf8(),
                   inventory=host_local.get_related('inventory').id,
                   job_type='scan',
                   project=None,
                   credential=ssh_credential.id,
                   playbook='Default', )
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


@pytest.fixture(scope="function")
def job_template_ask_variables_on_launch(job_template_ping):
    return job_template_ping.patch(ask_variables_on_launch=True)


@pytest.fixture(scope="function")
def job_template_with_ssh_connection(request, testsetup, ansible_facts,
                                     authtoken, api_job_templates_pg, project,
                                     ssh_credential_with_ssh_key_data_and_sudo, host_with_default_connection):
    '''Define a job_template that uses a machine credential that uses 'ssh',
    not a 'local' connection.'''

    # Create job_template
    payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                   description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                   inventory=host_with_default_connection.get_related('inventory').id,
                   job_type='run',
                   project=project.id,
                   credential=ssh_credential_with_ssh_key_data_and_sudo.id,
                   verbosity=4,
                   playbook='site.yml', )  # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.fixture(scope="function")
def optional_survey_spec():
    # TODO - add an optional question for each question type
    payload = dict(name=fauxfactory.gen_utf8(),
                   description=fauxfactory.gen_utf8(),
                   spec=[dict(required=False,
                              question_name="Enter your email &mdash; &euro;",
                              variable="submitter_email",
                              type="text",
                              default="mjones@maffletrox.edu"),
                         dict(required=False,
                              question_name="Enter your employee number email &mdash; &euro;",
                              variable="employee_number",
                              type="integer",)])
    return payload


@pytest.fixture(scope="function")
def required_survey_spec():
    # TODO - add a required question for each question type
    payload = dict(name=fauxfactory.gen_utf8(),
                   description=fauxfactory.gen_utf8(),
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
                              type="text"),
                         dict(required=False,
                              question_name="Test question",
                              variable="intersection",
                              type="text",
                              default="survey"), ])
    return payload


@pytest.fixture(scope="function")
def job_template_variables_needed_to_start(job_template_ping, required_survey_spec):
    obj = job_template_ping.patch(survey_enabled=True)
    obj.get_related('survey_spec').post(required_survey_spec)
    return obj


@pytest.fixture(scope="function")
def job_template_passwords_needed_to_start(job_template_ping, ssh_credential_multi_ask):
    return job_template_ping.patch(credential=ssh_credential_multi_ask.id)


@pytest.fixture(scope="function")
def files_scan_job_template(scan_job_template):
    '''Scan job template with files enabled.'''
    variables = dict(scan_file_paths="/tmp,/bin")
    return scan_job_template.patch(extra_vars=json.dumps(variables))


@pytest.fixture(scope="function")
def job_template_with_schedule(request, authtoken, job_template):
    """A job template with an associated schedule
    """

    obj = job_template.get_related('schedules').post({
        "name": "test_schedule-%s" % fauxfactory.gen_utf8(),
        "description": "every day for 1 time",
        "enabled": True,
        "rrule": "DTSTART:20160213T050000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1",
        "extra_data": {}
    })

    request.addfinalizer(obj.silent_delete)

    return job_template
