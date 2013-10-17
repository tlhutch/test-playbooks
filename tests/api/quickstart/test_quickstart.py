import os
import re
import httplib
import pytest
import yaml
from inflect import engine
from unittestzero import Assert
from common.api.schema import validate
from common.yaml_file import load_file
from tests.api import Base_Api_Test

def find_object(api, base_url, **kwargs):
    r = api.get(base_url, kwargs)
    assert r.status_code == httplib.OK
    data = r.json()

    # FIXME ... perform some assertions on the data?
    return data.get('results')

# Load configuration
cfg = load_file(os.path.join(os.path.dirname(__file__), 'data.yaml'))

# Initialize inflection engine
inflect = engine()

# Parameterize tests based on yaml configuration
def pytest_generate_tests(metafunc):

    # FIXME ... access the value of a fixture?
    # Wouldn't it be nice if one could use datafile() here?

    for fixture in metafunc.fixturenames:
        test_set = list()
        id_list = list()

        # plural - parametrize entire list
        # (e.g. if asked for organizations, give _all_ organizations)
        if fixture in cfg:
            test_set.append(cfg[fixture])
            id_list.append(fixture)

        # singular - parametrize every time on list
        # (e.g. if asked for organization, parametrize _each_ organization)
        elif inflect.plural_noun(fixture) in cfg:
            key = inflect.plural_noun(fixture)
            for value in cfg[key]:
                test_set.append(value)
                if 'name' in value:
                    id_list.append(value['name'])
                elif 'username' in value:
                    id_list.append(value['username'])

        if test_set and id_list:
            metafunc.parametrize(fixture, test_set, ids=id_list)

@pytest.mark.usefixtures("authtoken")
@pytest.mark.incremental
class Test_Quickstart_Scenario(Base_Api_Test):

    @pytest.mark.destructive
    def test_organization_post(self, api, api_organizations, organization):

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
            pytest.xfail("Organization already exists")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/organizations', 'post')

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
    def test_users_post(self, api, api_users, user):

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
            pytest.xfail("User already exists")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/users', 'post')

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
    def test_users_add_user_to_org(self, api, api_users, api_organizations, organization):
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
    def test_create_user_credential(self, api, api_users, api_credentials, user):
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
    def test_inventory_post(self, api, api_inventory, api_organizations, inventory):

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
            pytest.xfail("inventory already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/inventories', 'post')

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
    def test_groups_post(self, api, api_groups, api_inventory, group):
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
            pytest.xfail("Group already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/groups', 'post')

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
    def test_hosts_post(self, api, api_hosts, api_inventory, host):
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
            pytest.xfail("host already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/hosts', 'post')

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
    def test_add_host_to_group(self, api, api_hosts, api_groups, host):
        # Find desired host
        host_id = find_object(api, api_hosts, \
            name=host['name'])[0].get('id', None)

        groups = find_object(api, api_groups, \
            name__in=','.join([grp for grp in host['groups']]))

        if not groups:
            pytest.skip("Not all hosts are associated with a group")

        for group in groups:
            # Add host to group
            payload = dict(id=host_id)
            r = api.post(group['related']['hosts'], payload)
            assert r.status_code == httplib.NO_CONTENT
            assert r.text == ''

    @pytest.mark.destructive
    def test_project_post(self, api, api_projects, api_organizations, awx_config, project, ansible_runner):

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
                dest="%s/%s" % ( awx_config['project_base_dir'], \
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
            pytest.xfail("project already created")
        else:
            assert r.status_code == httplib.CREATED
            validate(data, '/projects', 'post')

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
    def test_job_templates_post(self, api, api_inventory, api_credentials, api_projects, api_job_templates, job_template):
        # Find desired object identifiers
        inventory_id = find_object(api, api_inventory, name__exact=job_template['inventory'])[0]['id']
        credential_id = find_object(api, api_credentials, name__exact=job_template['credential'])[0]['id']
        project_id = find_object(api, api_projects, name__exact=job_template['project'])[0]['id']

        # Create a new job_template
        payload = dict(name=job_template['name'],
                       description=job_template.get('description',None),
                       job_type=job_template['job_type'],
                       playbook=job_template['playbook'],
                       inventory=inventory_id,
                       project=project_id,
                       credential=credential_id,
                       allow_callbacks=job_template.get('allow_callbacks', False),
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
    def test_job_templates_get(self, api, api_inventory, api_credentials, api_projects, api_job_templates, job_templates):
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
    def test_jobs_launch(self, api, api_job_templates, api_jobs, job_template):
        # Find desired object identifiers
        template = find_object(api, api_job_templates, name__iexact=job_template['name'])[0]

        # Create the job
        payload = dict(name=template['name'], # Add Date?
                       job_template=template['id'],
                       inventory=template['inventory'],
                       project=template['project'],
                       playbook=template['playbook'],
                       credential=template['credential'],)
        r = api.post(api_jobs, payload)
        assert r.status_code == httplib.CREATED
        data = r.json()
        validate(data, '/jobs', 'post')

        # Remember related.start link
        start_link = data.get('related',{}).get('start',None)

        # Determine if job is able to start
        r = api.get(start_link)
        assert r.status_code == httplib.OK
        data = r.json()
        # FIXME - validate json
        assert data['can_start']

        # FIXME - Figure out which passwords are needed
        payload = dict()
        for pass_field in data.get('passwords_needed_to_start', []):
            payload[pass_field] = 'thisWillFail'

        # Determine if job is able to start
        r = api.post(start_link, payload)
        assert r.status_code == httplib.ACCEPTED
