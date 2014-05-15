import pytest
import json
import common.utils
import common.exceptions
from tests.api import Base_Api_Test

@pytest.fixture(scope="function")
def extra_vars(request):
    return json.dumps(dict(overloaded=False))

@pytest.fixture(scope="function")
def prompt_extra_vars(request):
    return json.dumps(dict(overloaded=True, fail=False))

@pytest.fixture(scope="class")
def ansible_default_ipv4(request, ansible_facts):
    '''Return the ansible_default_ipv4 from ansible_facts of the system under test.'''
    return ansible_facts['ansible_default_ipv4']['address']

@pytest.fixture(scope="function")
def inventory_localhost(request, authtoken, api_hosts_pg, random_group, ansible_default_ipv4):
    '''Create a random inventory host where ansible_ssh_host == ansible_default_ipv4.'''
    payload = dict(name="random_host_alias - %s" % common.utils.random_ascii(),
                   description="host-%s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host='localhost', ansible_connection="local")),
                   inventory=random_group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=random_group.id))
    return obj

@pytest.fixture(scope="function")
def job_template_no_credential(request, authtoken, api_job_templates_pg, project_ansible_helloworld_hg, inventory_localhost, extra_vars):
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with no credential - %s" % common.utils.random_unicode(),
                   inventory=inventory_localhost.inventory,
                   job_type='run',
                   limit=inventory_localhost.name,
                   extra_vars=extra_vars,
                   project=project_ansible_helloworld_hg.id,
                   playbook='pass_unless.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def job_template_prompt_vars(request, authtoken, api_job_templates_pg, project_ansible_helloworld_hg, inventory_localhost, random_ssh_credential, extra_vars):
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with vars_prompt_on_launch - %s" % common.utils.random_unicode(),
                   inventory=inventory_localhost.inventory,
                   job_type='run',
                   limit=inventory_localhost.name,
                   credential=random_ssh_credential.id,
                   vars_prompt_on_launch=True,
                   extra_vars=extra_vars,
                   project=project_ansible_helloworld_hg.id,
                   playbook='fail_unless.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def job_template_prompt_pass(request, authtoken, api_job_templates_pg, project_ansible_helloworld_hg, inventory_localhost, random_ssh_credential_ask, extra_vars):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with ASK credential - %s" % common.utils.random_unicode(),
                   inventory=inventory_localhost.inventory,
                   job_type='run',
                   limit=inventory_localhost.name,
                   credential=random_ssh_credential_ask.id,
                   extra_vars=extra_vars,
                   project=project_ansible_helloworld_hg.id,
                   playbook='pass_unless.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def job_template_prompt_multipass(request, authtoken, api_job_templates_pg, project_ansible_helloworld_hg, inventory_localhost, random_ssh_credential_multi_ask, extra_vars):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with multi-ASK credential - %s" % common.utils.random_unicode(),
                   inventory=inventory_localhost.inventory,
                   job_type='run',
                   limit=inventory_localhost.name,
                   credential=random_ssh_credential_multi_ask.id,
                   extra_vars=extra_vars,
                   project=project_ansible_helloworld_hg.id,
                   playbook='pass_unless.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def job_template_prompt_multipass_vars(request, authtoken, api_job_templates_pg, project_ansible_helloworld_hg, inventory_localhost, random_ssh_credential_multi_ask, extra_vars):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with multi-ASK credential and vars_prompt_on_launch - %s" % common.utils.random_unicode(),
                   inventory=inventory_localhost.inventory,
                   job_type='run',
                   limit=inventory_localhost.name,
                   credential=random_ssh_credential_multi_ask.id,
                   vars_prompt_on_launch=True,
                   extra_vars=extra_vars,
                   project=project_ansible_helloworld_hg.id,
                   playbook='fail_unless.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Launch_Prompts(Base_Api_Test):
    '''
    Verify that appropriately configured job_templates prompt the user before launching.
    Scenarios include:
      * launching a job with no credential
      * launching a job with a password:ASK credential
      * launching a job with a password:ASK, sudo_password:ASK and ssh_keyunlock credential
      * launching a job with a vars_prompt_on_launch
      * launching a job with a vars_prompt_on_launch and password:ASK, sudo_password:ASK and ssh_keyunlock credential
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000', 'inventory_localhost')

    def test_no_credential(self, job_template_no_credential):
        assert not job_template_no_credential.vars_prompt_on_launch
        assert job_template_no_credential.credential is None

        # POST a job
        job_pg = job_template_no_credential.post_job()

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']
        assert 'passwords_needed_to_start' in start_pg.json
        assert 'vars_prompt_on_launch' in start_pg.json
        assert not start_pg.json['passwords_needed_to_start']
        assert not start_pg.json['vars_prompt_on_launch']

        # POST to start
        start_pg.post()

        # Wait 10mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*10)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_prompt_vars(self, job_template_prompt_vars, prompt_extra_vars):
        assert job_template_prompt_vars.vars_prompt_on_launch
        assert job_template_prompt_vars.credential is not None

        # POST a job
        job_pg = job_template_prompt_vars.post_job()

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']
        assert 'passwords_needed_to_start' in start_pg.json
        assert 'vars_prompt_on_launch' in start_pg.json
        assert not start_pg.json['passwords_needed_to_start']
        assert start_pg.json['vars_prompt_on_launch']

        # PATCH extra_vars to simulate how the UI prompts
        job_pg = job_pg.patch(extra_vars=prompt_extra_vars)
        assert prompt_extra_vars == job_pg.extra_vars

        # AssertionError: assert {'fail': False, 'overloaded': True} == '{"fail": false, "overloaded": true}'

        # POST to start
        start_pg.post()

        # Wait 10mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*10)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_prompt_pass(self, job_template_prompt_pass):
        assert not job_template_prompt_pass.vars_prompt_on_launch
        assert job_template_prompt_pass.credential is not None

        # POST a job
        job_pg = job_template_prompt_pass.post_job()

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']
        assert 'passwords_needed_to_start' in start_pg.json
        assert 'vars_prompt_on_launch' in start_pg.json
        assert start_pg.json['passwords_needed_to_start']
        assert not start_pg.json['vars_prompt_on_launch']

        # POST to start
        passwords = dict(ssh_password="Doesn't matter")
        start_pg.post(passwords)

        # Wait 10mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*10)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_prompt_multipass(self, job_template_prompt_multipass):
        assert not job_template_prompt_multipass.vars_prompt_on_launch
        assert job_template_prompt_multipass.credential is not None

        # POST a job
        job_pg = job_template_prompt_multipass.post_job()

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']
        assert 'passwords_needed_to_start' in start_pg.json
        assert 'vars_prompt_on_launch' in start_pg.json
        assert start_pg.json['passwords_needed_to_start'], 'expecting non-empty list of passwords needed to start'
        assert len(start_pg.json['passwords_needed_to_start']) > 1, 'expecting multiple passwords to start'
        assert not start_pg.json['vars_prompt_on_launch']

        # POST to start
        passwords = dict(ssh_password="Doesn't matter", sudo_password="Still doesn't matter")
        start_pg.post(passwords)

        # Wait 10mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*10)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_prompt_multipass_vars(self, job_template_prompt_multipass_vars, prompt_extra_vars):
        assert job_template_prompt_multipass_vars.vars_prompt_on_launch
        assert job_template_prompt_multipass_vars.credential is not None

        # POST a job
        job_pg = job_template_prompt_multipass_vars.post_job()

        # GET related->start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']
        assert 'passwords_needed_to_start' in start_pg.json
        assert 'vars_prompt_on_launch' in start_pg.json
        assert start_pg.json['passwords_needed_to_start'], 'expecting non-empty list of passwords needed to start'
        assert len(start_pg.json['passwords_needed_to_start']) > 1, 'expecting multiple passwords to start'
        assert start_pg.json['vars_prompt_on_launch']

        # PATCH extra_vars to simulate how the UI prompts
        job_pg = job_pg.patch(extra_vars=prompt_extra_vars)
        assert prompt_extra_vars == job_pg.extra_vars

        # POST to start
        passwords = dict(ssh_password="Doesn't matter", sudo_password="Still doesn't matter")
        start_pg.post(passwords)

        # Wait 10mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*10)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
