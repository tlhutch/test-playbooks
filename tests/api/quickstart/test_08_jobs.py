import os
import re
import pytest
import httplib
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

@pytest.fixture(scope="module")
def api_jobs(request):
    '''
    Navigate the API and return a link to jobs
    '''
    api = request.getfuncargvalue('api')
    api_version = request.config.getvalue('api_version')

    if api_version == 'current_version':
        api_jobs = api.get('/api/').json().get('current_version')
    else:
        api_jobs = api.get('/api/').json().get('available_versions').get(api_version, None)

    Assert.not_none(api_jobs, "Unsupported api-version specified: %s" % api_version)

    return api.get(api_jobs).json().get('jobs')


@pytest.fixture(scope="module",
                params=["language_features/ansible_pull.yml",
                        "language_features/loop_plugins.yml",
                        "language_features/register_logic.yml",
                        "language_features/batch_size_control.yml",
                        "language_features/file_secontext.yml",
                        "language_features/loop_with_items.yml",
                        "language_features/roletest2.yml",
                        "language_features/complex_args.yml",
                        "language_features/get_url.yml",
                        "language_features/roletest.yml",
                        "language_features/conditionals_part1.yml",
                        "language_features/group_by.yml",
                        "language_features/nested_playbooks.yml",
                        "language_features/selective_file_sources.yml",
                        "language_features/conditionals_part2.yml",
                        "language_features/group_commands.yml",
                        "language_features/tags.yml",
                        "language_features/custom_filters.yml",
                        "language_features/intermediate_example.yml",
                        "language_features/upgraded_vars.yml",
                        "language_features/delegation.yml",
                        "language_features/intro_example.yml",
                        "language_features/prompts.yml",
                        "language_features/user_commands.yml",
                        "language_features/environment.yml",
                        "language_features/loop_nested.yml",
                       ])
def template_playbook(request):
    return request.param

class Test_Jobs(Base_Api_Test):
    @pytest.mark.nondestructive
    def test_unauthorized(self, api, api_jobs):
        r = api.get(api_jobs)
        assert r.status_code == httplib.UNAUTHORIZED
        validate(r.json(), '/jobs', 'unauthorized')

    @pytest.mark.nondestructive
    def test_authorized(self, api, api_jobs):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        # Get list of available jobs
        data = api.get(api_jobs).json()

        # Validate schema
        validate(data, '/jobs', 'get')

    @pytest.mark.destructive
    def test_create_job(self, api, api_jobs, api_base, template_playbook):
        # login
        api.login(self.testsetup.credentials['default']['username'],
                  self.testsetup.credentials['default']['password'])

        def find_object(otype, **kwargs):
            data = api.get(api_base + otype, kwargs).json()
            for k,v in kwargs.items():
                k = re.sub(r'__.*', '', k)
                assert data.get('results')[0][k] == v
            return data.get('results')[0]

        # Find desired object identifiers
        inventory_id = find_object('inventories', name='Web Servers').get('id', None)
        credential_id = find_object('credentials', name__iexact='root (ask)').get('id', None)
        project_id = find_object('projects', name__iexact='ansible-examples').get('id', None)
        template = find_object('job_templates', name__iexact=os.path.basename(template_playbook))

        # Create the job
        payload = dict(name=template.get('name'), # Add Date?
                       description=template.get('description'),
                       job_template=template.get('id'),
                       inventory=inventory_id,
                       project=project_id,
                       playbook=template_playbook,
                       credential=credential_id,)
        r = api.post(api_jobs, payload)
        data = r.json()
        assert r.status_code == httplib.CREATED
        validate(data, '/jobs', 'post')

        # Remember related.start link
        start_link = data.get('related',{}).get('start',None)

        # Determine if job is able to start
        r = api.get(start_link)
        assert r.status_code == httplib.OK
        data = r.json()
        # FIXME - validate json
        assert data['can_start']

        # Figure out which passwords are needed
        payload = dict()
        for pass_field in data.get('passwords_needed_to_start', []):
            payload[pass_field] = 'password' # Insert a valid password

        # Determine if job is able to start
        r = api.post(start_link, payload)
        assert r.status_code == httplib.ACCEPTED
