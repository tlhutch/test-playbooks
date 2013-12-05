import os
import sys
import re
import httplib
import pytest
import time
from inflect import engine
from unittestzero import Assert
from common.api.schema import validate
from common.yaml_file import load_file
from tests.api import Base_Api_Test
from common.exceptions import Duplicate_Exception, NoContent_Exception

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
            for (count, value) in enumerate(cfg[key]):
                test_set.append(value)
                if 'name' in value:
                    id_list.append(value['name'])
                elif 'username' in value:
                    id_list.append(value['username'])
                else:
                    id_list.append('item%d' % count)

        if test_set and id_list:
            metafunc.parametrize(fixture, test_set, ids=id_list)

@pytest.mark.usefixtures("authtoken")
@pytest.mark.incremental
@pytest.mark.integration
class Test_Quickstart_Scenario(Base_Api_Test):

    @pytest.mark.destructive
    def test_environment_setup(self, ansible_runner):
        '''
        This test is a hack to make sure all test systems have the proper
        passwd
        '''

        # Set rootpw to something we know
        assert self.has_credentials('ssh', fields=['username', 'password'])
        ansible_runner.shell("echo '{username}:{password}' | chpasswd".format(**self.credentials['ssh']))

        # Increase MaxSessions and MaxStartups
        ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?MaxSessions .*", line="MaxSessions 150")
        ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?MaxStartups .*", line="MaxStartups 150")

        # Enable PasswordAuth (disabled on AWS instances)
        ansible_runner.lineinfile(dest="/etc/ssh/sshd_config", regexp="^#?PasswordAuthentication .*", line="PasswordAuthentication yes")

        # Restart sshd
        try:
            # RPM-based distros call the service: sshd
            ansible_runner.service(name="sshd", state="restarted")
        except Exception, e:
            # Ubuntu calls the service: ssh
            ansible_runner.service(name="ssh", state="restarted")

    @pytest.mark.destructive
    def test_install_license(self, awx_config, tmpdir, ansible_runner):
        # FIXME - parameterize the license info and store it in data.yml

        if awx_config['license_info'].get('valid_key', False) and \
           awx_config['license_info'].get('compliant', False):
            pytest.xfail("License key already activated")

        assert 'license' in cfg, \
            "No license information found in test configuration"

        print cfg['license']

        # Create license script
        py_script = '''#!/usr/bin/python
import time
from datetime import datetime, timedelta
try:
    from awx.main.licenses import LicenseWriter
except ImportError:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from awx.main.licenses import LicenseWriter

def to_seconds(itime):
    return int(float(time.mktime(itime.timetuple())))

if __name__ == '__main__':

    writer = LicenseWriter(
        company_name   = "{company_name}",
        contact_name   = "{contact_name}",
        contact_email  = "{contact_email}",
        instance_count = {instance_count},
        license_date   = to_seconds(datetime.now() + timedelta(days={license_days})),
    )

    fd = open('/etc/awx/license', 'w+')
    fd.write(writer.get_string())
    fd.close()
'''.format(**cfg['license'])
        p = tmpdir.mkdir("ansible").join("install_license.py")
        fd = p.open('w+')
        fd.write(py_script)
        fd.close()

        # Using ansible, copy script to target system
        ansible_runner.copy(src=fd.name, dest='/tmp/%s' % p.basename, mode='0755')

        # Using ansible, run the script
        ansible_runner.shell('python /tmp/%s' % p.basename, creates='/etc/awx/license')

    @pytest.mark.destructive
    def test_organizations_post(self, api_organizations_pg, organization):

        # Create a new organization
        payload = dict(name=organization['name'],
                       description=organization['description'])
        try:
            org = api_organizations_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_organization_get(self, api_organizations_pg, organizations):

        org_page = api_organizations_pg.get(name__in=','.join([o['name'] for o in organizations]))
        assert len(organizations) == len(org_page.results)

    @pytest.mark.destructive
    def test_users_post(self, api_users_pg, user):

        payload = dict(username=user['username'],
                       first_name=user['first_name'],
                       last_name=user['last_name'],
                       email=user['email'],
                       is_superuser=user['is_superuser'],
                       password=user['password'],)

        try:
            api_users_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_users_get(self, api_users_pg, users):
        user_page = api_users_pg.get(username__in=','.join([o['username'] for o in users]))
        assert len(users) == len(user_page.results)

    @pytest.mark.destructive
    def test_organizations_add_users(self, api_users_pg, api_organizations_pg, organization):
        # get org related users link
        matches = api_organizations_pg.get(name__iexact=organization['name']).results
        assert len(matches) == 1
        org_related_pg = matches[0].get_related('users')

        # Add each user to the org
        for username in organization.get('users', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent_Exception):
                org_related_pg.post(payload)

    @pytest.mark.destructive
    def test_organizations_add_admins(self, api_users_pg, api_organizations_pg, organization):
        # get org related users link
        matches = api_organizations_pg.get(name__iexact=organization['name']).results
        assert len(matches) == 1
        org_related_pg = matches[0].get_related('admins')

        # Add each user to the org
        for username in organization.get('admins', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent_Exception):
                org_related_pg.post(payload)

    @pytest.mark.destructive
    def test_teams_post(self, api_teams_pg, api_organizations_pg, team):
        # locate desired organization resource
        org_pg = api_organizations_pg.get(name__iexact=team['organization']).results[0]

        payload = dict(name=team['name'],
                       description=team['description'],
                       organization=org_pg.id)
        try:
            api_teams_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_teams_get(self, api_teams_pg, teams):
        team_page = api_teams_pg.get(name__in=','.join([o['name'] for o in teams]))
        assert len(teams) == len(team_page.results)

    @pytest.mark.destructive
    def test_teams_add_users(self, api_users_pg, api_teams_pg, team):
        # locate desired team resource
        matches = api_teams_pg.get(name__iexact=team['name']).results
        assert len(matches) == 1
        team_related_pg = matches[0].get_related('users')

        # Add specified users to the team
        for username in team.get('users', []):
            user = api_users_pg.get(username__iexact=username).results.pop()

            # Add user to org
            payload = dict(id=user.id)
            with pytest.raises(NoContent_Exception):
                team_related_pg.post(payload)

    @pytest.mark.destructive
    def test_credentials_post(self, api_users_pg, api_teams_pg, api_credentials_pg, credential):

        # build credential payload
        payload = dict(name=credential['name'],
                       description=credential['description'],
                       kind=credential['kind'],
                       username=credential.get('username', None),
                       password=credential.get('password', None),
                       cloud=credential.get('cloud', False),
                      )

        # Add user id (optional)
        if credential['user']:
            user_pg = api_users_pg.get(username__iexact=credential['user']).results[0]
            payload['user'] = user_pg.id

        # Add team id (optional)
        if credential['team']:
            team_pg = api_teams_pg.get(name__iexact=credential['team']).results[0]
            payload['team'] = team_pg.id

        # Add machine/scm credential fields
        if credential['kind'] in ('ssh', 'scm'):
            # Assert the required credentials available?
            fields = ['username', 'password', 'ssh_key_data', 'ssh_key_unlock', ]
            if credential['kind'] in ('ssh'):
                fields += ['sudo_username', 'sudo_password']
            # The value 'encrypted' is not included in 'fields' because it is
            # *not* a valid payload key
            assert self.has_credentials(credential['kind'], fields=fields + ['encrypted'])

            # Merge with credentials.yaml
            payload.update(dict( \
                ssh_key_data=credential.get('ssh_key_data', ''),
                ssh_key_unlock=credential.get('ssh_key_unlock', ''),
                sudo_username=credential.get('sudo_username', ''),
                sudo_password=credential.get('sudo_password', ''),))

            # Apply any variable substitution
            for field in fields:
                payload[field] = payload[field].format(**self.credentials[credential['kind']])

        # Merge with cloud credentials.yaml
        if credential['cloud']:
            fields = ['username', 'password']
            assert self.has_credentials('cloud', credential['kind'], fields=fields)
            for field in fields:
                payload[field] = payload[field].format(**self.credentials['cloud'][credential['kind']])

        try:
            org = api_credentials_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_credentials_get(self, api_credentials_pg, credentials):
        credential_page = api_credentials_pg.get(or__name=[o['name'] for o in credentials])
        assert len(credentials) == len(credential_page.results)

    @pytest.mark.destructive
    def test_inventories_post(self, api_inventories_pg, api_organizations_pg, inventory):

        # Find desired org
        matches = api_organizations_pg.get(name__iexact=inventory['organization']).results
        assert len(matches) == 1
        org = matches.pop()

        # Create a new inventory
        payload = dict(name=inventory['name'],
                       description=inventory['description'],
                       organization=org.id,)

        try:
            api_inventories_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_inventories_get(self, api_inventories_pg, inventories):
        # Get list of created inventories
        api_inventories_pg.get(name__in=','.join([o['name'] for o in inventories]))

        # Validate number of inventories found
        assert len(inventories) == len(api_inventories_pg.results)

    @pytest.mark.destructive
    def test_groups_post(self, api_groups_pg, api_inventories_pg, group):
        # Find desired inventory
        inventory_id = api_inventories_pg.get(name__iexact=group['inventory']).results[0].id

        # Create a new inventory
        payload = dict(name=group['name'],
                       description=group['description'],
                       inventory=inventory_id,)

        # different behavior depending on if we're creating child or parent
        if 'parent' in group:
            parent_pg = api_groups_pg.get(name__exact=group['parent']).results[0]
            new_group_pg = parent_pg.get_related('children')
        else:
            new_group_pg = api_groups_pg

        try:
            new_group_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_groups_get(self, api_groups_pg, groups):

        # Get list of created groups
        api_groups_pg.get(name__in=','.join([o['name'] for o in groups]))

        # Validate number of inventories found
        assert len(groups) == len(api_groups_pg.results)

    @pytest.mark.destructive
    def test_hosts_post(self, api_hosts_pg, api_inventories_pg, host):
        # Find desired inventory
        inventory_id = api_inventories_pg.get(name__iexact=host['inventory']).results[0].id

        # Create a new host
        payload = dict(name=host['name'],
                       description=host['description'],
                       inventory=inventory_id,
                       variables=host.get('variables',''))

        try:
            api_hosts_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_hosts_get(self, api_hosts_pg, hosts):
        # Get list of available hosts
        api_hosts_pg.get(name__in=','.join([o['name'] for o in hosts]))

        # Validate number of inventories found
        assert len(hosts) == api_hosts_pg.count

    @pytest.mark.destructive
    def test_hosts_add_group(self, api_hosts_pg, api_groups_pg, host):
        # Find desired host
        host_id = api_hosts_pg.get(name=host['name']).results[0].id

        # Find desired groups
        groups = api_groups_pg.get(name__in=','.join([grp for grp in host['groups']])).results

        if not groups:
            pytest.skip("Not all hosts are associated with a group")

        # Add host to associated groups
        payload = dict(id=host_id)
        for group in groups:
            groups_host_pg = group.get_related('hosts')
            with pytest.raises(NoContent_Exception):
                groups_host_pg.post(payload)

    @pytest.mark.destructive
    def test_inventory_sources_patch(self, api_groups_pg, api_credentials_pg, inventory_source):
        # Find desired group
        group_pg = api_groups_pg.get(name__iexact=inventory_source['group']).results[0]

        # Find desired credential
        credential_pg = api_credentials_pg.get(name__iexact=inventory_source['credential']).results[0]

        # Get Page groups->related->inventory_source
        inventory_source_pg = group_pg.get_related('inventory_source')

        payload = dict(source=inventory_source['source'],
                       source_regions=inventory_source.get('source_regions', ''),
                       source_vars=inventory_source.get('source_vars', ''),
                       source_tags=inventory_source.get('source_tags', ''),
                       credential=credential_pg.id,
                       overwrite=inventory_source.get('overwrite', False),
                       overwrite_vars=inventory_source.get('overwrite_vars', False),
                       update_on_launch=inventory_source.get('update_on_launch', False),
                       update_interval=inventory_source.get('update_interval', 0),
                      )
        inventory_source_pg.patch(**payload)

    @pytest.mark.destructive
    def test_inventory_sources_update(self, api_groups_pg, api_inventory_sources_pg, inventory_source):
        # Find desired group
        group_id = api_groups_pg.get(name__iexact=inventory_source['group']).results[0].id

        # Find inventory source
        inv_src = api_inventory_sources_pg.get(group=group_id).results[0]

        # Navigate to related -> update
        inv_update_pg = inv_src.get_related('update')

        # Ensure inventory_source is ready for update
        assert inv_update_pg.json['can_update']

        # Trigger inventory_source update
        inv_update_pg.post()

    @pytest.mark.nondestructive
    @pytest.mark.jira('AC-596', run=False)
    def test_inventory_sources_update_status(self, api_groups_pg, api_inventory_sources_pg, inventory_source):
        # Find desired group
        group_id = api_groups_pg.get(name__iexact=inventory_source['group']).results[0].id

        # Find desired inventory_source
        inv_src = api_inventory_sources_pg.get(group=group_id).results[0]

        # Navigate to related -> inventory_updates
        # last_update only appears *after* the update completes
        # inv_updates_pg = inv_src.get_related('last_update')
        # Warning, the following sssumes the first update is the most recent
        inv_updates_pg = inv_src.get_related('inventory_updates').results[0]

        # Ensure the update completed successfully
        timeout = 60 * 5 # 5 minutes
        start_time = time.time()
        wait_timeout = start_time + timeout
        status = inv_updates_pg.status.lower()
        while status in ['new', 'pending', 'waiting', 'running']:
            inv_updates_pg.get()
            status = inv_updates_pg.status.lower()
            assert wait_timeout > time.time(), "Timeout exceeded (%s seconds) waiting for inventory_source update to complete (status:%s)" % (time.time() - start_time, status)
            # time.sleep(1)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert 'successful' == inv_updates_pg.status.lower(), \
            "Inventory update unsuccessful (%s)\nUpdate result_stdout: %s\nUpdate result_traceback: %s" % \
            (inv_updates_pg.status, inv_updates_pg.result_stdout, inv_updates_pg.result_traceback)
        assert 'Traceback' not in inv_updates_pg.result_traceback
        assert 'Traceback' not in inv_updates_pg.result_stdout

    @pytest.mark.nondestructive
    def test_inventory_sources_get_hosts(self, api_groups_pg, api_hosts_pg, inventory_source):
        # Find desired group
        group = api_groups_pg.get(name__iexact=inventory_source['group']).results[0]

        # Find hosts matching the group
        group_hosts_pg = group.get_related('hosts')

        # Validate number of inventories found
        assert group_hosts_pg.count > 0, "No hosts were synced for group '%s'" % group.name

    @pytest.mark.destructive
    def test_projects_post(self, api_projects_pg, api_organizations_pg, api_credentials_pg, awx_config, project, ansible_runner):

        # Checkout repository on the target system
        if project['scm_type'] in [None, 'manual'] \
           and 'scm_url' in project:
            assert '_ansible_module' in project, \
                "Must provide ansible module to use for scm_url: %s " % project['scm_url']

            # Make sure the required package(s) are installed
            results = ansible_runner.shell("test -f /etc/system-release && yum -y install %s || true" \
                % project['_ansible_module'])
            results = ansible_runner.shell("grep -qi ubuntu /etc/os-release && apt-get install %s || true" \
                % project['_ansible_module'])

            # Clone the repo
            clone_func = getattr(ansible_runner, project['_ansible_module'])
            results = clone_func(
                force='no',
                repo=project['scm_url'],
                dest="%s/%s" % ( awx_config['project_base_dir'], \
                    project['local_path']))

        # Find desired object identifiers
        org_id = api_organizations_pg.get(name__iexact=project['organization']).results[0].id

        # Build payload
        payload = dict(name=project['name'],
                       description=project['description'],
                       organization=org_id,
                       scm_type=project['scm_type'],)

        # Add scm_type specific values
        if project['scm_type'] in [None, 'manual']:
            payload['local_path'] = project['local_path']
        else:
            payload.update(dict(scm_url=project['scm_url'],
                                scm_branch=project.get('scm_branch',''),
                                scm_clean=project.get('scm_clean', False),
                                scm_delete_on_update=project.get('scm_delete_on_update', False),
                                scm_update_on_launch=project.get('scm_update_on_launch', False),))

        # Add credential (optional)
        if 'credential' in project:
            credential_id = api_credentials_pg.get(name__iexact=project['credential']).results[0].id
            payload['credential'] = credential_id

        # Create project
        try:
            api_projects_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_projects_get(self, api_projects_pg, projects):
        api_projects_pg.get(or__name=[o['name'] for o in projects])
        assert len(projects) == len(api_projects_pg.results)

    @pytest.mark.destructive
    def test_projects_update(self, api_projects_pg, api_organizations_pg, project):
        # Find desired project
        matches = api_projects_pg.get(name__iexact=project['name'], scm_type=project['scm_type'])
        assert matches.count == 1
        project_pg = matches.results.pop()

        # Assert that related->update matches expected
        update_pg = project_pg.get_related('update')
        if project['scm_type'] in [None, 'manual']:
            assert not update_pg.json['can_update'], "Manual projects should not be updateable"
            pytest.skip("Manual projects can not be updated")
        else:
            assert update_pg.json['can_update'], "SCM projects must be updateable"

            # Has an update already been triggered?
            if 'last_update' in project_pg.json['related'] or \
               'current_update' in project_pg.json['related']:
                # FIXME - maybe we should still update?
                pytest.xfail("Project already updated")
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
    def test_projects_update_status(self, api_projects_pg, api_organizations_pg, project):

        # Find desired project
        matches = api_projects_pg.get(name__iexact=project['name'], scm_type=project['scm_type'])
        assert matches.count == 1
        project_pg = matches.results.pop()

        # Assert that related->update matches expected
        update_pg = project_pg.get_related('update')
        if project['scm_type'] in [None, 'manual']:
            assert not update_pg.json['can_update'], "Manual projects should not be updateable"
        else:
            assert update_pg.json['can_update'], "SCM projects must be updateable"

        # Further inspect project updates
        project_updates_pg = project_pg.get_related('project_updates')
        if project['scm_type'] in [None, 'manual']:
            assert project_updates_pg.count == 0, "Manual projects do not support updates"
        else:
            assert project_updates_pg.count > 0, "SCM projects should update after creation, but no updates were found"

            latest_update_pg = project_updates_pg.results.pop()

            # Ensure the update successfully
            timeout = 60 * 5 # 5 minutes
            start_time = time.time()
            wait_timeout = start_time + timeout
            status = latest_update_pg.status.lower()
            while status in ['new', 'pending', 'waiting', 'running']:
                latest_update_pg.get()
                status = latest_update_pg.status.lower()
                assert wait_timeout > time.time(), "Timeout exceeded (%s seconds) waiting for project update completion (status:%s)" % (time.time() - start_time, status)
                # time.sleep(1)

            assert 'successful' == latest_update_pg.status.lower(), \
                "Project update unsuccessful (%s)\nUpdate result_stdout: %s\nUpdate result_traceback: %s" % \
                (latest_update_pg.status, latest_update_pg.result_stdout, latest_update_pg.result_traceback)
            assert not latest_update_pg.failed
            assert 'Traceback' not in latest_update_pg.result_traceback
            assert 'Traceback' not in latest_update_pg.result_stdout

    @pytest.mark.destructive
    def test_organizations_add_projects(self, api_organizations_pg, api_projects_pg, organization):
        # locate desired project resource
        matches = api_organizations_pg.get(name__iexact=organization['name']).results
        assert len(matches) == 1
        project_related_pg = matches[0].get_related('projects')

        projects = organization.get('projects', [])
        if not projects:
            pytest.skip("No projects associated with organization")

        # Add each team to the project
        for name in projects:
            project = api_projects_pg.get(name__iexact=name).results.pop()

            payload = dict(id=project.id)
            with pytest.raises(NoContent_Exception):
                project_related_pg.post(payload)

    @pytest.mark.jira('AC-641', run=True)
    @pytest.mark.destructive
    def test_job_templates_post(self, api_inventories_pg, api_credentials_pg, api_projects_pg, api_job_templates_pg, job_template):
        # Find desired object identifiers
        inventory_id = api_inventories_pg.get(name__iexact=job_template['inventory']).results[0].id
        project_id = api_projects_pg.get(name__iexact=job_template['project']).results[0].id

        # Create a new job_template
        payload = dict(name=job_template['name'],
                       description=job_template.get('description',None),
                       job_type=job_template['job_type'],
                       playbook=job_template['playbook'],
                       job_tags=job_template.get('job_tags', ''),
                       limit=job_template.get('limit', ''),
                       inventory=inventory_id,
                       project=project_id,
                       allow_callbacks=job_template.get('allow_callbacks', False),
                       verbosity=job_template.get('verbosity', 0),
                       forks=job_template.get('forks', 0),
                      )

        # Add credential identifiers
        for cred in ('credential', 'cloud_credential'):
            if cred in job_template:
                payload[cred] = api_credentials_pg.get(name__iexact=job_template[cred]).results[0].id

        try:
            api_job_templates_pg.post(payload)
        except Duplicate_Exception, e:
            pytest.xfail("Already exists")

    @pytest.mark.nondestructive
    def test_job_templates_get(self, api_job_templates_pg, job_templates):
        api_job_templates_pg.get(or__name=[o['name'] for o in job_templates])
        assert len(job_templates) == len(api_job_templates_pg.results)

    @pytest.mark.destructive
    def test_jobs_launch(self, api_job_templates_pg, api_jobs_pg, job_template):
        # Find desired object identifiers
        template_pg = api_job_templates_pg.get(name__iexact=job_template['name']).results[0]

        # Create the job
        payload = dict(name=template_pg.name, # Add Date?
                       job_template=template_pg.id,
                       inventory=template_pg.inventory,
                       project=template_pg.project,
                       playbook=template_pg.playbook,
                       credential=template_pg.credential,)
        job_pg = api_jobs_pg.post(payload)

        # Determine if job is able to start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']

        # FIXME - Figure out which passwords are needed
        payload = dict()
        for pass_field in start_pg.json.get('passwords_needed_to_start', []):
            payload[pass_field] = 'thisWillFail'

        # Launch job
        start_pg.post(payload)

    @pytest.mark.nondestructive
    def test_jobs_launch_status(self, api_job_templates_pg, api_jobs_pg, job_template):

        # Find desired object identifiers
        template_pg = api_job_templates_pg.get(name__iexact=job_template['name']).results[0]

        # Find the most recently launched job for the desired job_template
        matches = api_jobs_pg.get(job_template=template_pg.id, order_by='-id')
        assert matches.results > 0, "No jobs matching job_template=%s found" % template_pg.id
        job_pg = matches.results[0]

        # The job should already have launched ... and shouldn't be start'able
        start_pg = job_pg.get_related('start')
        assert not start_pg.json['can_start']

        # Ensure the launch completed successfully
        timeout = 60 * 5 # 5 minutes
        start_time = time.time()
        wait_timeout = start_time + timeout
        status = job_pg.status.lower()
        while status in ['new', 'pending', 'waiting', 'running']:
            job_pg.get()
            status = job_pg.status.lower()
            assert wait_timeout > time.time(), "Timeout exceeded (%s seconds) waiting for job completion (status:%s)" % (time.time() - start_time, status)
            # time.sleep(1)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert 'successful' == job_pg.status.lower(), \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback)
        assert 'Traceback' not in job_pg.result_traceback
        assert 'Traceback' not in job_pg.result_stdout
