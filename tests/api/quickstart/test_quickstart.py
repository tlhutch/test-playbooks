import os
import re
import httplib
import pytest
import yaml
from common.api.schema import validate
from tests.api import Base_Api_Test
from unittestzero import Assert

def find_object(api, base_url, **kwargs):
    r = api.get(base_url, kwargs)
    assert r.status_code == httplib.OK
    data = r.json()

    # FIXME ... perform some assertions on the data?
    return data.get('results')

# Override global awx_data fixture to support a local datafile
@pytest.fixture(scope="module")
def awx_data(request, datafile):
    return yaml.load(datafile('data.yaml'))

@pytest.fixture(scope="module")
def organizations(request, awx_data):
    return awx_data['organizations']

@pytest.fixture(scope="module")
def users(request, awx_data):
    return awx_data['users']

@pytest.fixture(scope="module")
def inventories(request, awx_data):
    return awx_data['inventories']

@pytest.fixture(scope="module")
def groups(request, awx_data):
    return awx_data['groups']

@pytest.fixture(scope="module")
def hosts(request, awx_data):
    return awx_data['hosts']

@pytest.fixture(scope="module")
def projects(request, awx_data):
    return awx_data['projects']

@pytest.fixture(scope="module")
def job_templates(request, awx_data):
    return awx_data['job_templates']

@pytest.fixture(scope="module")
def jobs(request, awx_data):
    return awx_data['jobs']

@pytest.fixture(scope="class",
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
                        "language_features/loop_nested.yml",])
def template_playbook(request):
    return request.param

@pytest.mark.usefixtures("authtoken")
@pytest.mark.incremental
class Test_Quickstart_Scenario(Base_Api_Test):

    @pytest.mark.destructive
    def test_organization_post(self, api, api_organizations, organizations):

        xfail = False
        for organization in organizations:
            # Create a new organization
            payload = dict(name=organization['name'],
                           description=organization['description'])
            r = api.post(api_organizations, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST and \
                data.get('name','') == ['Organization with this Name already exists.']:
                Assert.equal(r.status_code, httplib.BAD_REQUEST)
                validate(data, '/organizations', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/organizations', 'post')
        if xfail:
            pytest.xfail("Organization already exists")

    @pytest.mark.nondestructive
    def test_organization_get(self, api, api_organizations, organizations):

        # Get list of available organizations
        params = dict(name__in=','.join([o['name'] for o in organizations]))
        r = api.get(api_organizations, params=params)
        assert r.status_code == httplib.OK
        data = r.json()

        # validate schema
        validate(data, '/organizations', 'get')

        num_orgs = len(data.get('results',[]))
        Assert.true(num_orgs == len(organizations), \
            'Expecting %s organizations, found %s' % \
            (len(organizations), num_orgs))

    @pytest.mark.destructive
    def test_users_post(self, api, api_users, users):

        xfail = False
        # Create users
        for user in users:
            payload = dict(username=user['username'],
                           first_name=user['first_name'],
                           last_name=user['last_name'],
                           email=user['email'],
                           is_superuser=user['is_superuser'],
                           password=user['password'],)
            r = api.post(api_users, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST and \
               data.get('username','') == ['User with this Username already exists.']:
                Assert.equal(r.status_code, httplib.BAD_REQUEST)
                validate(data, '/users', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/users', 'post')

        if xfail:
            pytest.xfail("User already exists")

    @pytest.mark.nondestructive
    def test_users_get(self, api, api_users, users):
        # Get list of created users
        params = dict(username__in=','.join([o['username'] for o in users]))
        r = api.get(api_users, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(data, '/users', 'get')

        # Validate number of users found
        num_users = len(data.get('results',[]))
        Assert.true(num_users == len(users), 'Expecting %s users (%s)' \
            % (len(users), num_users))

    @pytest.mark.destructive
    def test_users_add_user_to_org(self, api, api_users, api_organizations, organizations):
        for organization in organizations:
            # Find desired org
            org_users_link = find_object(api, api_organizations, \
                name__iexact=organization['name'])[0]['related']['users']

            for user in organization.get('users', []):
                # Find the desired user
                user_id = find_object(api, api_users, \
                    username__iexact=user)[0]['id']

                # Add user to org
                payload = dict(id=user_id)
                r = api.post(org_users_link, payload)

                assert r.status_code == httplib.NO_CONTENT
                assert r.text == ''

    @pytest.mark.destructive
    def test_create_user_credential(self, api, api_users, api_credentials, users):
        for user in users:
            # Find the desired user
            record = find_object(api, api_users, \
                username__iexact=user['username'])[0]
            user_id = record['id']
            user_credentials_link = record['related']['credentials']

            # create user credentials
            for cred in user.get('credentials', []):
                payload = dict(name=cred['name'],
                               description=cred['description'],
                               ssh_username=cred['ssh_username'],
                               ssh_password=cred['ssh_password'],
                               user=user_id)
                r = api.post(user_credentials_link, payload)
                assert r.status_code == httplib.CREATED
                validate(r.json(), '/credentials', 'post')

    @pytest.mark.destructive
    def test_inventory_post(self, api, api_inventory, api_organizations, inventories):
        xfail = False
        for inventory in inventories:

            # Find desired org
            org_id = find_object(api, api_organizations, \
                name__iexact=inventory['organization'])[0]['id']

            # Create a new inventory
            payload = dict(name=inventory['name'],
                           description=inventory['description'],
                           organization=org_id,)
            r = api.post(api_inventory, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST:
                validate(data, '/inventories', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/inventories', 'post')
        if xfail:
            pytest.xfail("inventory already created")

    @pytest.mark.nondestructive
    def test_inventory_get(self, api, api_inventory, inventories):
        # Get list of created inventories
        params = dict(name__in=','.join([o['name'] for o in inventories]))
        r = api.get(api_inventory, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(data, '/inventories', 'get')

        # Validate number of inventories found
        num_inventories = len(data.get('results',[]))
        Assert.true(num_inventories == len(inventories), 'Expecting %s inventories (%s)' \
            % (len(inventories), num_inventories))

    @pytest.mark.destructive
    def test_groups_post(self, api, api_groups, api_inventory, groups):
        xfail = False
        for group in groups:
            # Find desired org
            inventory_id = find_object(api, api_inventory, \
                name__iexact=group['inventory'])[0]['id']

            # Create a new inventory
            payload = dict(name=group['name'],
                           description=group['description'],
                           inventory=inventory_id,)
            r = api.post(api_groups, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST:
                validate(data, '/groups', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/groups', 'post')

        if xfail:
            pytest.xfail("Group already created")

    @pytest.mark.nondestructive
    def test_groups_get(self, api, api_groups, groups):

        # Get list of created groups
        params = dict(name__in=','.join([o['name'] for o in groups]))
        r = api.get(api_groups, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(data, '/groups', 'get')

        # Validate number of inventories found
        num_found = len(data.get('results',[]))
        Assert.true(num_found == len(groups), 'Expecting %s, found %s' \
            % (len(groups), num_found))

    @pytest.mark.destructive
    def test_hosts_post(self, api, api_hosts, api_inventory, hosts):
        xfail = True
        for host in hosts:
            inventory_id = find_object(api, api_inventory, \
                name=host['inventory'])[0].get('id', None)

            # Create a new host
            payload = dict(name=host['name'],
                           description=host['description'],
                           inventory=inventory_id,
                           variables=host.get('variables',''))

            r = api.post(api_hosts, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST:
                validate(data, '/hosts', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/hosts', 'post')

        if xfail:
            pytest.xfail("host already created")

    @pytest.mark.nondestructive
    def test_hosts_get(self, api, api_hosts, hosts):
        # Get list of available hosts
        params = dict(name__in=','.join([o['name'] for o in hosts]))
        r = api.get(api_hosts, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(r.json(), '/hosts', 'get')

        # Validate number of inventories found
        num_found = len(data.get('results',[]))
        Assert.true(num_found == len(hosts), 'Expecting %s, found %s' \
            % (len(hosts), num_found))

    @pytest.mark.destructive
    def test_add_host_to_group(self, api, api_hosts, api_groups, hosts):
        skip = False
        for host in hosts:
            # Find desired host
            host_id = find_object(api, api_hosts, \
                name=host['name'])[0].get('id', None)

            groups = find_object(api, api_groups, \
                name__in=','.join([grp for grp in host['groups']]))

            if not groups:
                skip = True

            for group in groups:
                # Add host to group
                payload = dict(id=host_id)
                r = api.post(group['related']['hosts'], payload)
                assert r.status_code == httplib.NO_CONTENT
                assert r.text == ''

        if skip:
            pytest.skip("Not all hosts are associated with a group")

    @pytest.mark.destructive
    def test_create_projects(self, api, api_projects, api_organizations, api_config, projects, ansible_runner):
        xfail = False
        for project in projects:

            # Checkout repository on the target system
            if project['scm_type'] in [None, 'menual'] \
               and 'scm_url' in project:
                assert '_ansible_module' in project, \
                    "Must provide ansible module to use for scm_url: %s " % project['scm_url']
                # Make sure the required package(s) are installed
                results = ansible_runner.yum(
                    name=project['_ansible_module'],
                    state='installed')

                # Clone the repo
                clone_func = getattr(ansible_runner, project['_ansible_module'])
                results = clone_func(
                    force='no',
                    repo=project['scm_url'],
                    dest="%s/%s" % ( api_config['project_base_dir'], \
                        project['local_path']))

            # Find desired org
            org_id = find_object(api, api_organizations, \
                name=project['organization'])[0].get('id', None)

            # Create a new project
            payload = dict(name=project['name'],
                           description=project['description'],
                           organization=org_id,
                           local_path=project['local_path'],
                           scm_type=project['scm_type'],)
            r = api.post(api_projects, payload)
            data = r.json()

            # support idempotency
            if r.status_code == httplib.BAD_REQUEST:
                validate(data, '/projects', 'duplicate')
                xfail = True
            else:
                assert r.status_code == httplib.CREATED
                validate(data, '/projects', 'post')

        if xfail:
            pytest.xfail("project already created")

    @pytest.mark.nondestructive
    def test_projects_get(self, api, api_projects, projects):
        # Get list of available hosts
        params = dict(name__in=','.join([o['name'] for o in projects]))
        r = api.get(api_projects, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(r.json(), '/projects', 'get')

        # Validate number of inventories found
        num_found = len(data.get('results',[]))
        Assert.true(num_found == len(projects), 'Expecting %s, found %s' \
            % (len(projects), num_found))

    @pytest.mark.destructive
    def test_job_templates_post(self, api, api_job_templates, api_base, template_playbook):
        # Find desired object identifiers
        inventory_id = find_object(api, api_inventory, name='Web Servers').get('id', None)
        credential_id = find_object(api, api_credentials, name__iexact='root (ask)').get('id', None)
        project_id = find_object(api, api_projects, name__iexact='ansible-examples').get('id', None)

        # Create a new job_template
        payload = dict(name=os.path.basename(template_playbook),
                       description="Check run for %s" % template_playbook,
                       job_type="check",
                       inventory=inventory_id,
                       project=project_id,
                       credential=credential_id,
                       playbook=template_playbook,
                       allow_callbacks=False
                      )
        r = api.post(api_job_templates, payload)
        data = r.json()

        # support idempotency
        if r.status_code == httplib.BAD_REQUEST:
            validate(data, '/job_templates', 'duplicate')
            pytest.xfail("project already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/job_templates', 'post')

    @pytest.mark.nondestructive
    def test_job_templates_get(self, api, api_job_templates, job_templates):
        # Get list of available hosts
        params = dict(name__in=','.join([o['name'] for o in job_templates]))
        r = api.get(api_job_templates, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(r.json(), '/job_templates', 'get')

        # Validate number of inventories found
        num_found = len(data.get('results',[]))
        Assert.true(num_found == len(job_templates), 'Expecting %s, found %s' \
            % (len(job_templates), num_found))

    @pytest.mark.destructive
    def test_jobs_create_job(self, api, api_jobs, api_base, template_playbook):
        def find_object(otype, **kwargs):
            data = api.get(api_base + otype, kwargs).json()
            for k,v in kwargs.items():
                k = re.sub(r'__.*', '', k)
                assert data.get('results')[0][k] == v
            return data.get('results')[0]

        # Find desired object identifiers
        inventory_id = find_object('inventory', name='Web Servers').get('id', None)
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

    @pytest.mark.nondestructive
    def test_jobs_get(self, api, api_jobs, jobs):
        # Get list of available hosts
        params = dict(name__in=','.join([o['name'] for o in jobs]))
        r = api.get(api_jobs, params=params)
        assert r.status_code == httplib.OK

        # Validate schema
        data = r.json()
        validate(r.json(), '/jobs', 'get')

        # Validate number of inventories found
        num_found = len(data.get('results',[]))
        Assert.true(num_found == len(jobs), 'Expecting %s, found %s' \
            % (len(jobs), num_found))

