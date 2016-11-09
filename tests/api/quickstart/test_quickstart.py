from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging
import json
import os
import re

from towerkit.exceptions import BadRequest, Duplicate, NoContent
from towerkit.yaml_file import load_file
import towerkit.tower.license
from inflect import engine
import pytest

from tests.api import Base_Api_Test


# Parameterize tests based on yaml configuration
def pytest_generate_tests(metafunc):
    # Initialize inflection engine
    inflect = engine()

    # FIXME ... access the value of a fixture?
    # Wouldn't it be nice if one could use datafile() here?

    for fixture in metafunc.fixturenames:
        test_set = list()
        id_list = list()

        # HACK - to avoid fixture namespace collision, we prefix fixtures with
        # '_' in this module.  The following will identify such fixtures, and
        # find the appropriate YAML configuration.
        config_key = fixture
        if config_key.startswith('_'):
            config_key = config_key[1:]

        # plural - parametrize entire list
        # (e.g. if asked for organizations, give _all_ organizations)
        if config_key in metafunc.cls.config:
            test_set.append(metafunc.cls.config[config_key])
            id_list.append(fixture)

        # singular - parametrize every time on list
        # (e.g. if asked for organization, parametrize _each_ organization)
        elif inflect.plural_noun(config_key) in metafunc.cls.config:
            key = inflect.plural_noun(config_key)
            for (count, value) in enumerate(metafunc.cls.config[key]):
                test_set.append(value)
                if 'name' in value:
                    id_list.append(value['name'])
                elif 'username' in value:
                    id_list.append(value['username'])
                else:
                    id_list.append('item%d' % count)

        if test_set and id_list:
            metafunc.parametrize(fixture, test_set, ids=id_list)


@pytest.fixture(scope='class')
def install_integration_license(authtoken, api_config_pg, awx_config, tower_license_path, tower_aws_path):
    '''If a suitable license is not already installed, install a new license'''
    logging.debug("calling fixture install_integration_license")
    if not (awx_config['license_info'].get('valid_key', False) and
            awx_config['license_info'].get('compliant', False) and
            awx_config['license_info'].get('available_instances', 0) >= 10001):

        # Install/replace license
        logging.debug("installing license {0}".format(tower_license_path))
        license_json = towerkit.tower.license.generate_license(instance_count=10000, days=60, license_type='enterprise')
        api_config_pg.post(license_json)


@pytest.fixture(scope='class')
def update_sshd_config(ansible_runner):
    '''Update /etc/ssh/sshd_config to increase MaxSessions'''

    # Increase MaxSessions and MaxStartups
    ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?MaxSessions .*", line="MaxSessions 150")
    ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?MaxStartups .*", line="MaxStartups 150")
    # Enable PasswordAuth (disabled on AWS instances)
    ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?PasswordAuthentication .*", line="PasswordAuthentication yes")
    ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?ChallengeResponseAuthentication .*", line="ChallengeResponseAuthentication yes")
    # Permit root login
    ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?PermitRootLogin .*", line="PermitRootLogin yes")

    # Restart sshd
    # RPM-based distros call the service: sshd
    contacted = ansible_runner.service(name="sshd", state="restarted")
    # Ubuntu calls the service: ssh
    for result in contacted.values():
        if 'failed' in result and result['failed']:
            ansible_runner.service(name="ssh", state="restarted")


@pytest.fixture(scope='class')
def set_rootpw(ansible_runner, testsetup):
    '''Set the rootpw to something we use in credentials'''
    assert 'ssh' in testsetup.credentials, "No SSH credentials defined"
    assert 'username' in testsetup.credentials['ssh'], "No SSH username defined in credentials"
    assert 'password' in testsetup.credentials['ssh'], "No SSH password defined in credentials"
    ansible_runner.shell("echo '{username}:{password}' | chpasswd".format(**testsetup.credentials['ssh']))


@pytest.mark.incremental
@pytest.mark.integration
@pytest.mark.skip_selenium
@pytest.mark.trylast
class Test_Quickstart_Scenario(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures("authtoken", "install_integration_license", "update_sshd_config", "set_rootpw")

    # Load test configuration
    config = load_file(os.path.join(os.path.dirname(__file__), 'data.yml'))

    @pytest.mark.destructive
    def test_organizations_post(self, api_organizations_pg, _organization):
        # Create a new organization
        payload = dict(name=_organization['name'],
                       description=_organization['description'])
        try:
            api_organizations_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_organization_get(self, api_organizations_pg, _organizations):
        org_page = api_organizations_pg.get(or__name=[o['name'] for o in _organizations])
        assert len(_organizations) == org_page.count

    @pytest.mark.destructive
    def test_users_post(self, api_users_pg, _user):
        payload = dict(username=_user['username'],
                       first_name=_user['first_name'],
                       last_name=_user['last_name'],
                       email=_user['email'],
                       is_superuser=_user['is_superuser'],
                       password=_user['password'],)

        try:
            api_users_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_users_get(self, api_users_pg, _users):
        user_page = api_users_pg.get(username__in=','.join([o['username'] for o in _users]))
        assert len(_users) == user_page.count

    @pytest.mark.destructive
    def test_organizations_add_users(self, api_users_pg, api_organizations_pg, _organization):
        # get org related users link
        matches = api_organizations_pg.get(name__exact=_organization['name']).results
        assert len(matches) == 1
        org_related_pg = matches[0].get_related('users')

        # Add each user to the org
        for username in _organization.get('users', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent):
                org_related_pg.post(payload)

    @pytest.mark.destructive
    def test_organizations_add_admins(self, api_users_pg, api_organizations_pg, _organization):
        # get org related users link
        matches = api_organizations_pg.get(name__exact=_organization['name']).results
        assert len(matches) == 1
        org_related_pg = matches[0].get_related('admins')

        # Add each user to the org
        for username in _organization.get('admins', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent):
                org_related_pg.post(payload)

    @pytest.mark.destructive
    def test_teams_post(self, api_teams_pg, api_organizations_pg, _team):
        # locate desired organization resource
        org_pg = api_organizations_pg.get(name__exact=_team['organization']).results[0]

        payload = dict(name=_team['name'],
                       description=_team.get('description', ''),
                       organization=org_pg.id)
        try:
            api_teams_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_teams_get(self, api_teams_pg, _teams):
        teams = _teams
        team_page = api_teams_pg.get(name__in=','.join([o['name'] for o in teams]))
        assert len(teams) == team_page.count

    @pytest.mark.destructive
    def test_teams_add_users(self, api_users_pg, api_teams_pg, _team):
        # locate desired team resource
        matches = api_teams_pg.get(name__iexact=_team['name']).results
        assert len(matches) == 1
        team_related_pg = matches[0].get_related('users')

        # Add specified users to the team
        for username in _team.get('users', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent):
                team_related_pg.post(payload)

    @pytest.mark.destructive
    def test_credentials_post(self, api_users_pg, api_teams_pg, api_credentials_pg, _credential):
        # build credential payload
        payload = dict(name=_credential['name'],
                       description=_credential['description'],
                       kind=_credential['kind'],
                       username=_credential.get('username', None),
                       password=_credential.get('password', None),
                       cloud=_credential.get('cloud', False),)

        # Add user id (optional)
        if _credential['user']:
            user_pg = api_users_pg.get(username__iexact=_credential['user']).results[0]
            payload['user'] = user_pg.id

        # Add team id (optional)
        if _credential['team']:
            team_pg = api_teams_pg.get(name__iexact=_credential['team']).results[0]
            payload['team'] = team_pg.id

        # Add machine/scm credential fields
        if _credential['kind'] in ('ssh', 'scm'):
            # Assert the required credentials available?
            fields = ['username', 'password', 'ssh_key_data', 'ssh_key_unlock', ]
            if _credential['kind'] in ('ssh'):
                fields += ['become_username', 'become_password', 'vault_password']
            # The value 'encrypted' is not included in 'fields' because it is
            # *not* a valid payload key
            assert self.has_credentials(_credential['kind'], fields=fields + ['encrypted'])

            # Merge with credentials.yaml
            payload.update(dict(
                ssh_key_data=_credential.get('ssh_key_data', ''),
                ssh_key_unlock=_credential.get('ssh_key_unlock', ''),
                become_username=_credential.get('become_username', ''),
                become_password=_credential.get('become_password', ''),
                vault_password=_credential.get('vault_password', ''),))

            # Apply any variable substitution
            for field in fields:
                payload[field] = payload[field].format(**self.credentials[_credential['kind']])

        # Merge with cloud credentials.yaml
        if _credential['cloud']:
            if _credential['kind'] == 'gce':
                fields = ['username', 'project', 'ssh_key_data']
            elif _credential['kind'] == 'azure':
                fields = ['username', 'ssh_key_data']
            elif _credential['kind'] == 'vmware':
                fields = ['username', 'password', 'host']
            elif _credential['kind'] == 'openstack':
                fields = ['username', 'project', 'host', 'password']
            else:
                fields = ['username', 'password']
            for field in fields:
                if _credential['kind'] == 'azure':
                    assert self.has_credentials('cloud', 'azure_classic', fields=fields)
                    payload[field] = _credential[field].format(**self.credentials['cloud']['azure_classic'])
                else:
                    assert self.has_credentials('cloud', _credential['kind'], fields=fields)
                    payload[field] = _credential[field].format(**self.credentials['cloud'][_credential['kind']])
        try:
            print json.dumps(payload, indent=4)
            api_credentials_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_credentials_get(self, api_credentials_pg, _credentials):
        cred_names = [cred['name'] for cred in _credentials]
        # take 2.4 -> 3.0 azure credential rename into consideration
        azure_name = filter(lambda name: 'Azure' in name, cred_names).pop()
        cred_names.append(azure_name.replace(' Classic', ''))

        credential_page = api_credentials_pg.get(or__name=cred_names)
        assert(not credential_page.count % len(_credentials)
               ), "The number of credentials isn't cleanly divisible by the number of those recently added."

    @pytest.mark.destructive
    def test_inventory_scripts_post(self, api_inventory_scripts_pg, api_organizations_pg, _inventory_script):
        # Find desired org
        matches = api_organizations_pg.get(name__exact=_inventory_script['organization']).results
        assert len(matches) == 1
        org = matches.pop()

        # Create a new inventory
        payload = dict(name=_inventory_script['name'],
                       description=_inventory_script.get('description', ''),
                       organization=org.id,
                       script=_inventory_script.get('script', ''))

        try:
            api_inventory_scripts_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_inventory_scripts_get(self, api_inventory_scripts_pg, _inventory_scripts):
        # Get list of created inventories
        api_inventory_scripts_pg.get(or__name=[o['name'] for o in _inventory_scripts])

        # Validate number of inventories found
        assert len(_inventory_scripts) == api_inventory_scripts_pg.count

    @pytest.mark.destructive
    def test_inventories_post(self, api_inventories_pg, api_organizations_pg, _inventory):
        # Find desired org
        matches = api_organizations_pg.get(name__exact=_inventory['organization']).results
        assert len(matches) == 1
        org = matches.pop()

        # Create a new inventory
        payload = dict(name=_inventory['name'],
                       description=_inventory.get('description', ''),
                       organization=org.id)
        if 'variables' in _inventory:
            payload['variables'] = json.dumps(_inventory.get('variables'))

        try:
            api_inventories_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_inventories_get(self, api_inventories_pg, _inventories):
        # Get list of created inventories
        api_inventories_pg.get(or__name=[o['name'] for o in _inventories])

        # Validate number of inventories found
        assert len(_inventories) == api_inventories_pg.count

    @pytest.mark.destructive
    def test_groups_post(self, api_groups_pg, api_inventories_pg, _group):
        # Find desired inventory
        inventory_id = api_inventories_pg.get(name__iexact=_group['inventory']).results[0].id

        # Create a new inventory
        payload = dict(name=_group['name'],
                       description=_group.get('description', ''),
                       inventory=inventory_id)
        if 'variables' in _group:
            payload['variables'] = json.dumps(_group.get('variables'))

        # different behavior depending on if we're creating child or parent
        if 'parent' in _group:
            parent_pg = api_groups_pg.get(name__exact=_group['parent'], inventory=inventory_id).results[0]
            new_group_pg = parent_pg.get_related('children')
        else:
            new_group_pg = api_groups_pg

        try:
            new_group_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_groups_get(self, api_groups_pg, _groups):
        groups = _groups
        # Get list of created groups
        # NOTE: not__description="imported" will exclude groups created as part of an inventory_sync
        api_groups_pg.get(name__in=','.join([o['name'] for o in groups]), not__description="imported")

        # Validate number of inventories found
        assert len(groups) == api_groups_pg.count

    @pytest.mark.destructive
    def test_hosts_post(self, api_hosts_pg, api_inventories_pg, _host):
        host = _host
        # Find desired inventory
        inventory_id = api_inventories_pg.get(name__iexact=host['inventory']).results[0].id

        # Create a new host
        payload = dict(name=host['name'],
                       description=host.get('description', None),
                       inventory=inventory_id)
        if 'variables' in host:
            payload['variables'] = json.dumps(host.get('variables'))

        try:
            api_hosts_pg.post(payload)
        except Duplicate, e:
            pytest.skip(str(e))

    @pytest.mark.nondestructive
    def test_hosts_get(self, api_hosts_pg, api_inventories_pg, _hosts):
        # Get list of available hosts
        api_hosts_pg.get(or__name=[o['name'] for o in _hosts])

        # Validate number of hosts found while accounting for Demo inventory's use of localhost
        demo_count = api_inventories_pg.get(name__iexact="Demo Inventory").count
        assert len(_hosts) == api_hosts_pg.count - demo_count

    @pytest.mark.destructive
    def test_hosts_add_group(self, api_inventories_pg, api_hosts_pg, api_groups_pg, _host):
        # Find desired inventory
        inventory_id = api_inventories_pg.get(name__iexact=_host['inventory']).results[0].id

        # Find desired host considering Demo inventory's use of localhost
        hosts = api_hosts_pg.get(name=_host['name']).results
        host_id = [host for host in hosts if host.inventory == inventory_id][0].id

        # Find desired groups
        q_params = dict(inventory=inventory_id)
        group_names = _host.get('groups', None)
        if group_names:
            q_params.update(name__in=','.join([name for name in group_names]))
        groups = api_groups_pg.get(**q_params).results

        if not groups:
            pytest.skip("Not all hosts are associated with a group")

        # Add host to associated groups
        payload = dict(id=host_id)
        for group in groups:
            groups_host_pg = group.get_related('hosts')
            with pytest.raises(NoContent):
                groups_host_pg.post(payload)

    @pytest.mark.destructive
    def test_inventory_sources_patch(self, api_groups_pg, api_credentials_pg, api_inventory_scripts_pg, _inventory_source):
        # Find desired group
        group_pg = api_groups_pg.get(name__iexact=_inventory_source['group']).results[0]

        # Build payload
        payload = dict(source=_inventory_source['source'],
                       source_regions=_inventory_source.get('source_regions', ''),
                       source_vars=json.dumps(_inventory_source.get('source_vars', '')),
                       source_tags=_inventory_source.get('source_tags', ''),
                       overwrite=_inventory_source.get('overwrite', False),
                       overwrite_vars=_inventory_source.get('overwrite_vars', False),
                       update_on_launch=_inventory_source.get('update_on_launch', False),
                       update_interval=_inventory_source.get('update_interval', 0),)

        # Add the desired credential
        if 'credential' in _inventory_source:
            credential_pg = api_credentials_pg.get(name__iexact=_inventory_source['credential']).results[0]
            payload['credential'] = credential_pg.id

        # Add the desired source_script
        if 'source_script' in _inventory_source:
            script_pg = api_inventory_scripts_pg.get(name__iexact=_inventory_source['source_script']).results[0]
            payload['source_script'] = script_pg.id

        # Get Page groups->related->inventory_source
        inventory_source_pg = group_pg.get_related('inventory_source')

        # submit PATCH request
        inventory_source_pg.patch(**payload)

    @pytest.mark.destructive
    def test_inventory_sources_update(self, api_groups_pg, api_inventory_sources_pg, _inventory_source):
        # Find desired group
        group_id = api_groups_pg.get(name__iexact=_inventory_source['group']).results[0].id

        # Find inventory source
        inv_src = api_inventory_sources_pg.get(group=group_id).results[0]

        # Navigate to related -> update
        inv_update_pg = inv_src.get_related('update')

        # Ensure inventory_source is ready for update
        assert inv_update_pg.json['can_update']

        # Trigger inventory_source update
        inv_update_pg.post()

    @pytest.mark.nondestructive
    @pytest.mark.skip(reason='JIRA AC-596')
    def test_inventory_sources_update_status(self, api_groups_pg, api_inventory_sources_pg, _inventory_source):
        # Find desired group
        group_id = api_groups_pg.get(name__iexact=_inventory_source['group']).results[0].id

        # Find desired inventory_source
        inv_src = api_inventory_sources_pg.get(group=group_id).results[0]

        # Navigate to related -> inventory_updates
        #  * current_update only appears *during* the update is running
        #  * last_update only appears *after* the update completes
        inv_updates_pg = inv_src.get_related('inventory_updates', order_by='-id').results[0]

        # Wait for task to complete
        inv_updates_pg = inv_updates_pg.wait_until_completed(timeout=60 * 5)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert inv_updates_pg.is_successful, "Job unsuccessful - %s" % inv_updates_pg

        # Display output, even for success
        print inv_updates_pg.result_stdout

    @pytest.mark.nondestructive
    def test_inventory_sources_get_children(self, api_groups_pg, _inventory_source, region_choices):
        '''
        Tests that an inventory_sync created expected sub-groups
        '''
        # Find desired group
        group = api_groups_pg.get(name__iexact=_inventory_source['group']).results[0]

        # Find sub-groups
        children_pg = group.get_related('children')

        # Assert sub-groups were synced
        if children_pg.count == 0:
            pytest.skip("No sub-groups were created for inventory '%s'" % _inventory_source['name'])
        else:
            # Ensure all only groups matching source_regions were imported
            if 'source_regions' in _inventory_source and _inventory_source['source_regions'] != '':
                expected_source_regions = re.split(r'[,\s]+', _inventory_source['source_regions'])
                for child in children_pg.results:
                    # If the group is an official region (e.g. 'us-east-1' or
                    # 'ORD'), make sure it's one we asked for
                    if child.name in region_choices[_inventory_source['source']]:
                        assert child.name in expected_source_regions, \
                            "Imported region (%s) that wasn't in list of expected regions (%s)" % \
                            (child.name, expected_source_regions)
                    else:
                        print "Ignoring group '%s', it appears to not be a cloud region" % child.name

    @pytest.mark.destructive
    def test_projects_post(self, api_projects_pg, api_organizations_pg, api_credentials_pg, awx_config, _project, ansible_runner):
        # Checkout repository on the target system
        if _project['scm_type'] in [None, 'manual'] \
           and 'scm_url' in _project:
            assert '_ansible_module' in _project, \
                "Must provide ansible module to use for scm_url: %s " % _project['scm_url']

            # Make sure the required package(s) are installed
            results = ansible_runner.shell("test -f /etc/system-release && yum -y install %s || true"
                                           % _project['_ansible_module'])
            results = ansible_runner.shell("grep -qi ubuntu /etc/os-release && apt-get install %s || true"
                                           % _project['_ansible_module'])

            # Clone the repo
            clone_func = getattr(ansible_runner, _project['_ansible_module'])
            results = clone_func(
                force='no',
                repo=_project['scm_url'],
                dest=os.path.join(awx_config['project_base_dir'], _project['local_path']))
            assert 'failed' not in results, "Clone failed\n%s" % json.dumps(results, indent=4)

        # Find desired object identifiers
        org_id = api_organizations_pg.get(name__exact=_project['organization']).results[0].id

        # Build payload
        payload = dict(name=_project['name'],
                       description=_project['description'],
                       organization=org_id,
                       scm_type=_project['scm_type'],)

        # Add scm_type specific values
        if _project['scm_type'] in [None, 'manual']:
            payload['local_path'] = _project['local_path']
        else:
            payload.update(dict(scm_url=_project['scm_url'],
                                scm_branch=_project.get('scm_branch', ''),
                                scm_clean=_project.get('scm_clean', False),
                                scm_delete_on_update=_project.get('scm_delete_on_update', False),
                                scm_update_on_launch=_project.get('scm_update_on_launch', False),))

        # Add credential (optional)
        if 'credential' in _project:
            credential_id = api_credentials_pg.get(name__iexact=_project['credential']).results[0].id
            payload['credential'] = credential_id

        # Create project
        try:
            api_projects_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))
        except BadRequest, e:
            # Similar to Duplicate but occurs when all projects in local
            # directory are claimed (for repeated manual project runs).
            if "Invalid path choice" in e.message.get('local_path', [''])[0]:
                pytest.xfail(str(e))
            raise

    @pytest.mark.nondestructive
    def test_projects_get(self, api_projects_pg, _projects):
        api_projects_pg.get(or__name=[o['name'] for o in _projects])
        assert len(_projects) == api_projects_pg.count

    @pytest.mark.destructive
    def test_projects_update(self, api_projects_pg, api_organizations_pg, _project):
        # Find desired project
        matches = api_projects_pg.get(name__iexact=_project['name'], scm_type=_project['scm_type'])
        assert matches.count == 1
        project_pg = matches.results.pop()

        # Assert that related->update matches expected
        update_pg = project_pg.get_related('update')
        if _project['scm_type'] in [None, 'manual']:
            assert not update_pg.json['can_update'], "Manual projects should not be updateable"
            pytest.skip("Manual projects cannot be updated")
        else:
            assert update_pg.json['can_update'], "SCM projects must be updateable"

            # Has an update already been triggered?
            if 'current_update' in project_pg.json['related']:
                pytest.skip("Project update already queued")
            else:
                # Create password payload
                payload = dict()

                # Add required password fields (optional)
                assert self.has_credentials('scm')
                for field in update_pg.json.get('passwords_needed_to_update', []):
                    credential_field = field
                    if field == 'scm_password':
                        credential_field = 'password'
                    payload[field] = self.credentials['scm'][credential_field]

                # Initiate update
                update_pg.post(payload)

    @pytest.mark.nondestructive
    def test_projects_update_status(self, api_projects_pg, api_organizations_pg, _project):
        # Find desired project
        matches = api_projects_pg.get(name__iexact=_project['name'], scm_type=_project['scm_type'])
        assert matches.count == 1
        project_pg = matches.results.pop()

        # Assert that related->update matches expected
        update_pg = project_pg.get_related('update')
        if _project['scm_type'] in [None, 'manual']:
            assert not update_pg.json['can_update'], "Manual projects should not be updateable"
        else:
            assert update_pg.json['can_update'], "SCM projects must be updateable"

        # Further inspect project updates
        project_updates_pg = project_pg.get_related('project_updates')
        if _project['scm_type'] in [None, 'manual']:
            assert project_updates_pg.count == 0, "Manual projects do not support updates"
        else:
            assert project_updates_pg.count > 0, "SCM projects should update after creation, but no updates were found"

            latest_update_pg = project_updates_pg.results.pop()

            # Wait 8mins for job to complete
            latest_update_pg = latest_update_pg.wait_until_completed()

            # Make sure there is no traceback in result_stdout or result_traceback
            assert latest_update_pg.is_successful, "Job unsuccessful - %s" % latest_update_pg

            # Display output, even for success
            print latest_update_pg.result_stdout

    @pytest.mark.destructive
    def test_organizations_add_projects(self, api_organizations_pg, api_projects_pg, _organization):
        # locate desired project resource
        matches = api_organizations_pg.get(name__exact=_organization['name']).results
        assert len(matches) == 1
        project_related_pg = matches[0].get_related('projects')

        projects = _organization.get('projects', [])
        if not projects:
            pytest.skip("No projects associated with organization")

        # Add each team to the project
        for name in projects:
            project = api_projects_pg.get(name__iexact=name).results.pop()

            payload = dict(id=project.id)
            with pytest.raises(NoContent):
                project_related_pg.post(payload)

    @pytest.mark.destructive
    def test_job_templates_post(self, api_inventories_pg, api_credentials_pg, api_projects_pg,
                                api_job_templates_pg, _job_template, ansible_facts, ansible_runner):
        # Find desired object identifiers
        inventory_id = api_inventories_pg.get(name__iexact=_job_template['inventory']).results[0].id
        if _job_template.get('project', None):
            project_id = api_projects_pg.get(name__iexact=_job_template['project']).results[0].id
        else:
            project_id = None

        # Create a new job_template
        payload = dict(
            name=_job_template['name'],
            description=_job_template.get('description', None),
            job_type=_job_template['job_type'],
            playbook=_job_template['playbook'],
            job_tags=_job_template.get('job_tags', ''),
            limit=_job_template.get('limit', ''),
            inventory=inventory_id,
            project=project_id,
            allow_callbacks=_job_template.get('allow_callbacks', False),
            verbosity=_job_template.get('verbosity', 0),
            forks=_job_template.get('forks', 0)
        )

        # Optionally include extra_vars
        if 'extra_vars' in _job_template:
            payload['extra_vars'] = json.dumps(_job_template['extra_vars'])

        # Add credential identifiers
        for cred in ('credential', 'cloud_credential'):
            if cred in _job_template:
                matches = api_credentials_pg.get(name__iexact=_job_template[cred])
                assert(matches.count)
                payload[cred] = matches.results[0].id

        try:
            api_job_templates_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))

    @pytest.mark.nondestructive
    def test_job_templates_get(self, api_job_templates_pg, _job_templates):
        api_job_templates_pg.get(or__name=[o['name'] for o in _job_templates])
        assert len(_job_templates) == api_job_templates_pg.count

    @pytest.mark.destructive
    def test_jobs_launch(self, api_job_templates_pg, api_jobs_pg, _job_template):
        # If desired, skip launch
        if not _job_template.get('_launch', True):
            pytest.skip("Per-request, skipping launch: %s" % _job_template['name'])

        # Find desired object identifiers
        template_pg = api_job_templates_pg.get(name__iexact=_job_template['name']).results[0]

        # Build payload
        payload = dict(
            name=template_pg.name,  # Add Date?
            job_template=template_pg.id,
            inventory=template_pg.inventory,
            project=template_pg.project,
            playbook=template_pg.playbook,
            credential=template_pg.credential
        )

        # Post the job
        job_pg = api_jobs_pg.post(payload)

        # Determine if job is able to start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']

        # Provide requested credentials
        passwords = dict()
        for field in start_pg.json.get('passwords_needed_to_start', []):
            if field in self.credentials['ssh']:
                passwords[field] = self.credentials['ssh'][field]
            if field == 'ssh_password':
                passwords[field] = self.credentials['ssh']['password']
            if field == 'ssh_key_unlock':
                passwords[field] = self.credentials['ssh']['encrypted'][field]

        # Launch job
        start_pg.post(passwords)

    @pytest.mark.nondestructive
    @pytest.mark.github('https://github.com/ansible/ansible/issues/16801')
    def test_jobs_launch_status(self, api_job_templates_pg, api_jobs_pg, _job_template):
        # If desired, skip launch
        if not _job_template.get('_launch', True):
            pytest.skip("Per-request, skipping launch: %s" % _job_template['name'])

        # Find desired object identifiers
        template_pg = api_job_templates_pg.get(name__iexact=_job_template['name']).results[0]

        # Find the most recently launched job for the desired job_template
        matches = api_jobs_pg.get(job_template=template_pg.id, order_by='-id')
        assert matches.results > 0, "No jobs matching job_template=%s found" % template_pg.id
        job_pg = matches.results[0]

        # Wait 20mins for job to start (aka, enter 'pending' state)
        job_pg = job_pg.wait_until_started(timeout=60 * 20)

        # With the job started, it shouldn't be start'able anymore
        start_pg = job_pg.get_related('start')
        assert not start_pg.json['can_start'], \
            "Job id:%s launched (status:%s), but can_start: %s\n%s" % \
            (job_pg.id, job_pg.status, start_pg.json['can_start'], job_pg)

        # Wait 20mins for job to complete
        # TODO: It might be nice to wait 15 mins from when the job started
        job_pg = job_pg.wait_until_completed(timeout=60 * 20)

        # xfail for known vault packaging failure
        if job_pg.failed and 'ERROR: ansible-vault requires a newer version of pycrypto than the one installed on your platform.' in job_pg.result_stdout:
            pytest.xfail("Vault tests are expected to fail when tested with an older pycrypto")

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # Display output, even for success
        print job_pg.result_stdout

    @pytest.mark.destructive
    def test_schedules_post(self, api_unified_job_templates_pg, _schedule):
        matches = api_unified_job_templates_pg.get(name=_schedule['unified_job_template'])
        assert matches.count == 1, "Unexpected number of unified_job_templates found (%s != 1)" % matches.count

        # POST schedule
        schedules_pg = matches.results[0].get_related('schedules')
        utcnow = datetime.utcnow()
        dtstart = utcnow + relativedelta(minutes=-1)
        payload = dict(name=_schedule['name'],
                       description=_schedule.get('description', None),
                       enabled=_schedule.get('enabled', True),
                       unified_job_template=matches.results[0].id,
                       rrule=_schedule['rrule'].format(utcnow=utcnow, dtstart=dtstart.strftime("%Y%m%dT%H%M%SZ")))
        try:
            schedules_pg.post(payload)
        except Duplicate, e:
            pytest.xfail(str(e))
