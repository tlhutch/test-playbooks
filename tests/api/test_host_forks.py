import os
import pytest
import json
import tempfile
import time
import datetime
import common.utils
import common.tower.license
from tests.api import Base_Api_Test

NUM_HOSTS = 400
NUM_FORKS = 400

# The following fixture runs once for this entire module
@pytest.fixture(scope='module')
def backup_license(request, ansible_runner):
    ansible_runner.shell('test -f /etc/awx/aws && mv /etc/awx/aws /etc/awx/.aws', creates='/etc/awx/.aws', removes='/etc/awx/aws')
    ansible_runner.shell('test -f /etc/awx/license && mv /etc/awx/license /etc/awx/.license', creates='/etc/awx/.license', removes='/etc/awx/license')

    def teardown():
        ansible_runner.shell('test -f /etc/awx/.aws && mv /etc/awx/.aws /etc/awx/aws', creates='/etc/awx/aws', removes='/etc/awx/.aws')
        ansible_runner.shell('test -f /etc/awx/.license && mv /etc/awx/.license /etc/awx/license', creates='/etc/awx/license', removes='/etc/awx/.license')
    request.addfinalizer(teardown)

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_license(request, ansible_runner):
    fname = common.tower.license.generate_license_file(instance_count=NUM_HOSTS*10, days=7)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

@pytest.fixture(scope="class")
def organization(request, testsetup, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_ascii())
    testsetup.api.login(*testsetup.credentials['default'].values())
    obj = api_organizations_pg.post(payload)
    #request.addfinalizer(obj.delete)

    return obj

@pytest.fixture(scope="class")
def credential(request, testsetup, api_credentials_pg, api_users_pg):
    testsetup.api.login(*testsetup.credentials['default'].values())

    payload = dict(name="credential-%s" % common.utils.random_ascii(), kind='ssh')
    # Add user id
    admin = api_users_pg.get(username__exact='admin').results.pop()
    payload['user'] = admin.id

    obj = api_credentials_pg.post(payload)
    #request.addfinalizer(obj.delete)

    return obj

@pytest.fixture(scope="class")
def inventory(request, testsetup, ansible_runner, api_inventories_pg, api_groups_pg, api_hosts_pg, organization):
    # Create inventory
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   organization=organization.id,
                   variables=json.dumps(dict(ansible_connection='local')))
    testsetup.api.login(*testsetup.credentials['default'].values())
    inventory = api_inventories_pg.post(payload)
    #request.addfinalizer(inventory.delete)

    # Batch create group+hosts using awx-manage
    grp_name = "group-%s" % common.utils.random_ascii()
    inventory_dict = {grp_name: dict(hosts=[], vars={})}
    inventory_dict[grp_name]['hosts'] = ['host-%s' % num for num in range(NUM_HOSTS)]
    inventory_dict[grp_name]['vars'] = dict(ansible_connection='local')
    # inventory_dict['_meta'] = dict(hostvars=dict(ansible_ssh_host='localhost', connection='local'))
    # inventory_dict = {grp_name: dict(hosts=[], vars=[])}

    # Create an inventory script
    sh_script = '''#!/bin/bash
cat <<EOF
%s
EOF
''' % json.dumps(inventory_dict)
    (fd, fname) = tempfile.mkstemp(suffix='.sh')
    os.write(fd, sh_script)
    os.close(fd)

    # Copy script to test system
    remote_fname = '/tmp/%s' % os.path.basename(fname)
    ansible_runner.copy(src=fname, dest=remote_fname, mode='0755')

    # Run awx-manage inventory_import
    result = ansible_runner.shell('awx-manage inventory_import --inventory-name %s --source %s' \
        % (inventory.name, remote_fname))

    # Verify the import completed successfully
    assert result['rc'] == 0, "awx-manage inventory_import failed:\n[stdout]\n%s\n[stderr]\n%s" \
        % (result['stdout'], result['stderr'])

    return inventory

@pytest.fixture(scope="class")
def project(request, testsetup, api_projects_pg, organization):
    # Create project
    payload = dict(name="project-%s" % common.utils.random_ascii(),
                   organization=organization.id,
                   scm_type='hg',
                   scm_url='https://bitbucket.org/jlaska/ansible-helloworld',
                   scm_clean=False,
                   scm_delete_on_update=False,
                   scm_update_on_launch=False,)

    testsetup.api.login(*testsetup.credentials['default'].values())
    obj = api_projects_pg.post(payload)
    #request.addfinalizer(obj.delete)

    # Wait for project update to complete
    updates_pg = obj.get_related('project_updates')
    assert updates_pg.count > 0, 'No project updates found'
    latest_update_pg = updates_pg.results.pop()
    count = 0
    while count <30 and latest_update_pg.status.lower() != 'successful':
        latest_update_pg.get()
        count +=1

    return obj

@pytest.fixture(scope="class", params=[ \
    {'playbook': 'debug.yml', 'forks': 200, }, \
    {'playbook': 'debug.yml', 'forks': 400, }, \
    {'playbook': 'debug.yml', 'forks': 600, }, \
    {'playbook': 'debug.yml', 'forks': 800, }, \
    {'playbook': 'debug.yml', 'forks': 1000, }, \
    {'playbook': 'debug2.yml', 'forks': 200, }, \
    {'playbook': 'debug2.yml', 'forks': 400, }, \
    {'playbook': 'debug2.yml', 'forks': 600, }, \
    {'playbook': 'debug2.yml', 'forks': 800, }, \
    {'playbook': 'debug2.yml', 'forks': 1000, },])
def job_template(request, testsetup, api_job_templates_pg, inventory, project, credential):
    payload = dict(name="template-%s-%s" % (request.param, common.utils.random_ascii()),
                   job_type='run',
                   playbook=request.param['playbook'],
                   job_tags='',
                   limit='',
                   inventory=inventory.id,
                   project=project.id,
                   credential=credential.id,
                   allow_callbacks=False,
                   verbosity=0,
                   forks=request.param['forks'])
                   # forks=NUM_FORKS,)

    testsetup.api.login(*testsetup.credentials['default'].values())
    obj = api_job_templates_pg.post(payload)
    #request.addfinalizer(obj.delete)

    return obj

@pytest.mark.skip_selenium
@pytest.mark.usefixtures('backup_license', 'install_license')
class Test_Host_Fork(Base_Api_Test):

    @pytest.mark.usefixtures('authtoken')
    def test_awx_job_launch(self, api_jobs_pg, job_template):
        '''
        1) Launch the job_template
        2) Poll for status
        3) Assert results
        '''
        # Create the job
        payload = dict(name=job_template.name, # Add Date?
                       job_template=job_template.id,
                       inventory=job_template.inventory,
                       project=job_template.project,
                       playbook=job_template.playbook,
                       credential=job_template.credential,)
        job_pg = api_jobs_pg.post(payload)

        # Determine if job is able to start
        start_pg = job_pg.get_related('start')
        assert start_pg.json['can_start']

        # No passwords should be required to launch
        assert not start_pg.json.get('passwords_needed_to_start', [])

        # Launch job
        start_pg.post(payload)

        # Wait 20mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60*20)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback)
        assert 'Traceback' not in job_pg.result_traceback
        assert 'Traceback' not in job_pg.result_stdout

        created = datetime.datetime.strptime(job_pg.created, '%Y-%m-%dT%H:%M:%S.%fZ')
        modified = datetime.datetime.strptime(job_pg.modified, '%Y-%m-%dT%H:%M:%S.%fZ')
        delta = modified - created
        print "playbook:%s, forks:%s, runtime:%s (%s seconds)" % (job_template.playbook, job_template.forks, delta, delta.total_seconds())

    def test_ansible_job_launch(self, ansible_runner, inventory, job_template):

        pytest.skip("Not implemented")

        # Create static inventory file
        # Run play
        results = ansible_runner.shell('ansible-playbook -i /path/to/inventory, --forks FIXME /var/lib/awx/projects/*/FIXME')
        # Record results
