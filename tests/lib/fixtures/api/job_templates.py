import dateutil.rrule

from towerkit import rrule
import fauxfactory
import pytest


@pytest.fixture(scope="function")
def job_template_prompt_for_credential(factories, organization, project, host_local):
    """job_template with no machine credential and ask_credential_on_launch set to True"""
    return factories.job_template(description="job_template without credentials and "
                                              "ask_credential_on_launch set to True- %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project,
                                  inventory=host_local.ds.inventory,
                                  playbook='debug.yml',
                                  credential=None,
                                  ask_credential_on_launch=True)


@pytest.fixture(scope="function")
def job_template_no_credential(factories, organization, project, host_local):
    """job_template with no machine credential"""
    return factories.v2_job_template(description="job_template without credentials - %s" % fauxfactory.gen_utf8(),
                                     organization=organization, project=project,
                                     inventory=host_local.ds.inventory,
                                     playbook='debug.yml',
                                     credential=None)


@pytest.fixture(scope="function")
def job_template_with_random_limit(job_template):
    """job_template with a limit parameter that matches nothing"""
    return job_template.patch(limit='Random limit - %s' % fauxfactory.gen_utf8())


@pytest.fixture(scope="function")
def job_template_with_random_tag(factories, organization, project_ansible_git, ssh_credential, host_local):
    """job template with a tag parameter that matches nothing"""
    job_tag = fauxfactory.gen_utf8()

    return factories.job_template(description="job_template with tag - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project_ansible_git, credential=ssh_credential,
                                  inventory=host_local.ds.inventory,
                                  playbook='test/integration/targets/tags/test_tags.yml',
                                  job_tags=job_tag)


@pytest.fixture(scope="function")
def job_template_ask(factories, organization, project, ssh_credential_ask, host_local):
    """job template with an ASK credential"""
    return factories.job_template(description="job_template with ASK credential - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project, credential=ssh_credential_ask,
                                  inventory=host_local.ds.inventory, playbook='debug.yml')


@pytest.fixture(scope="function")
def job_template_multi_ask(factories, organization, project, ssh_credential_multi_ask, host_local):
    """job template with a multiple ASK credential"""
    return factories.job_template(description="job_template with multiple ASK credential - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project, credential=ssh_credential_multi_ask,
                                  inventory=host_local.ds.inventory, playbook='debug.yml')


@pytest.fixture(scope="function")
def job_template_ansible_playbooks_git(factories, organization, project_ansible_playbooks_git, ssh_credential,
                                       host_local):
    """job template whose project points to ansible-playbooks.git"""
    return factories.job_template(description="job_template using ansible-playbooks.git - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project_ansible_playbooks_git,
                                  credential=ssh_credential, inventory=host_local.ds.inventory,
                                  playbook='debug.yml')


@pytest.fixture(scope="function")
def job_template(factories, organization, project, ssh_credential, host_local):
    """job_template with a valid machine credential"""
    return factories.job_template(organization=organization, project=project, credential=ssh_credential,
                                  inventory=host_local.ds.inventory, playbook='debug.yml')


@pytest.fixture(scope="function")
def another_job_template(factories, organization, project, ssh_credential, host_local):
    """job_template with a valid machine credential"""
    return factories.job_template(organization=organization, project=project, credential=ssh_credential,
                                  inventory=host_local.ds.inventory, playbook='debug.yml')


@pytest.fixture(scope="function", params=['job_template_with_json_vars', 'job_template_with_yaml_vars'])
def job_template_with_extra_vars(request):
    """job_template with a set of extra_vars"""
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def job_template_with_json_vars(factories, organization, project, ssh_credential, host_local):
    """job_template with a set of JSON extra_vars"""
    return factories.job_template(description="job_template with extra_vars - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project, credential=ssh_credential,
                                  inventory=host_local.ds.inventory, playbook='debug.yml',
                                  extra_vars='{"jt_var": true, "intersection": "jt"}')


@pytest.fixture(scope="function")
def job_template_with_yaml_vars(factories, organization, project, ssh_credential, host_local):
    """job_template with a set of YAML extra_vars"""
    return factories.job_template(description="job_template with extra_vars - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project, credential=ssh_credential,
                                  inventory=host_local.ds.inventory, playbook='debug.yml',
                                  extra_vars="---\njt_var: true\nintersection: jt")


@pytest.fixture(scope="function")
def check_job_template(job_template):
    """basic check job_template"""
    return job_template.patch(job_type="check")


@pytest.fixture(scope="function")
def job_template_sleep(job_template_ansible_playbooks_git):
    """job_template that runs the sleep.yml playbook"""
    return job_template_ansible_playbooks_git.patch(playbook='sleep.yml')


@pytest.fixture(scope="function")
def job_template_ping(job_template_ansible_playbooks_git):
    """job_template that runs the ping.yml playbook"""
    return job_template_ansible_playbooks_git.patch(playbook='ping.yml')


@pytest.fixture(scope="function")
def api_job_templates_options_json(api_job_templates_pg):
    """Return job_template OPTIONS json"""
    return api_job_templates_pg.options().json


@pytest.fixture(scope="function")
def job_template_status_choices(api_job_templates_options_json):
    """Return job_template statuses from OPTIONS"""
    return dict(api_job_templates_options_json['actions']['GET']['status']['choices'])


@pytest.fixture(scope="function")
def job_template_ask_variables_on_launch(job_template_ping):
    """job_template that prompts for variables on launch"""
    return job_template_ping.patch(ask_variables_on_launch=True)


@pytest.fixture(scope="function")
def job_template_with_ssh_connection(factories, organization, project, ssh_credential_with_ssh_key_data_and_sudo,
                                     host_with_default_connection, ansible_facts):
    """job_template with a machine credential that uses 'ssh', instead of a 'local' connection"""
    return factories.job_template(description="job_template without credentials - %s" % fauxfactory.gen_utf8(),
                                  organization=organization, project=project,
                                  credential=ssh_credential_with_ssh_key_data_and_sudo,
                                  inventory=host_with_default_connection.ds.inventory, playbook='debug.yml',
                                  verbosity=4)


@pytest.fixture(scope="function")
def optional_survey_spec():
    # TODO - add an optional question for each question type
    return [dict(required=False,
                 question_name="Enter your email &mdash; &euro;",
                 variable="submitter_email",
                 type="text",
                 default="mjones@maffletrox.edu"),
            dict(required=False,
                 question_name="Enter your employee number email &mdash; &euro;",
                 variable="employee_number",
                 type="integer",)]


@pytest.fixture(scope="function")
def optional_survey_spec_without_defaults():
    # TODO - add an optional question for each question type
    return [dict(required=False,
                 question_name="Enter your email &mdash; &euro;",
                 variable="submitter_email",
                 type="text",),
            dict(required=False,
                 question_name="Enter your employee number email &mdash; &euro;",
                 variable="employee_number",
                 type="integer",)]


@pytest.fixture(scope="function")
def required_survey_spec():
    # TODO - add a required question for each question type
    return [dict(required=True,
                 question_name="Do you like chicken?",
                 question_description="Please indicate your chicken preference:",
                 variable="likes_chicken",
                 type="multiselect",
                 choices=['yes', 'no']),
            dict(required=True,
                 question_name="Favorite color?",
                 question_description="Pick a color darnit!",
                 variable="favorite_color",
                 type="multiplechoice",
                 choices=['red', 'green', 'blue'],
                 default="green"),
            dict(required=False,
                 question_name="Enter your email.",
                 variable="submitter_email",
                 type="text"),
            dict(required=False,
                 question_name="Survey variable.",
                 variable="survey_var",
                 type="text",
                 default="text"),
            dict(required=False,
                 question_name="Intersection variable.",
                 variable="intersection",
                 type="text",
                 default="survey")]


@pytest.fixture(scope="function")
def job_template_variables_needed_to_start(job_template_ping, required_survey_spec):
    """job_template with variables needed to start"""
    job_template_ping.add_survey(spec=required_survey_spec)
    return job_template_ping


@pytest.fixture(scope="function")
def job_template_passwords_needed_to_start(job_template_ping, ssh_credential_multi_ask):
    """job_template with passwords needed to start"""
    return job_template_ping.patch(credential=ssh_credential_multi_ask.id)


@pytest.fixture(scope="function")
def job_template_with_schedule(job_template):
    """job template with an associated schedule"""
    schedule_rrule = rrule.RRule(
        dateutil.rrule.DAILY, count=1, byminute='', bysecond='', byhour='')
    job_template.add_schedule(description="every day for 1 time", rrule='{0}'.format(schedule_rrule))
    return job_template


@pytest.fixture(scope="function")
def job_template_with_label(job_template, label):
    """job template with a randomly named label"""
    job_template.add_label(dict(id=label.id))
    return job_template.get()


@pytest.fixture(scope="function")
def job_template_with_labels(factories, job_template):
    """job template with three randomly named labels"""
    organization = job_template.ds.inventory.ds.organization

    # create three labels
    for i in range(3):
        label = factories.label(organization=organization)
        job_template.add_label(dict(id=label.id))
    return job_template.get()
