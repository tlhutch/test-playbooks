import os
import pytest
import json
import tempfile
import time
import datetime
import fauxfactory

from tests.api import Base_Api_Test


NUM_HOSTS = 100


@pytest.fixture(scope="class")
def inventory(request, ansible_runner, api_inventories_pg, api_groups_pg, api_hosts_pg, random_organization):
    # Create inventory
    payload = dict(name="inventory-%s" % fauxfactory.gen_utf8(),
                   organization=random_organization.id,
                   variables=json.dumps(dict(ansible_connection='local')))
    inventory = api_inventories_pg.post(payload)
    request.addfinalizer(inventory.delete)

    # Batch create group+hosts using awx-manage
    grp_name = "group-%s" % fauxfactory.gen_utf8()
    inventory_dict = {grp_name: dict(hosts=[], vars={})}
    inventory_dict[grp_name]['hosts'] = ['host-%s' % num for num in range(NUM_HOSTS)]
    inventory_dict[grp_name]['vars'] = dict(ansible_connection='local')
    # inventory_dict['_meta'] = dict(hostvars=dict(ansible_host='localhost', connection='local'))
    # inventory_dict = {grp_name: dict(hosts=[], vars=[])}

    # Create an inventory script
    sh_script = """#!/bin/bash
cat <<EOF
%s
EOF
""" % json.dumps(inventory_dict)
    (fd, fname) = tempfile.mkstemp(suffix='.sh')
    os.write(fd, sh_script)
    os.close(fd)

    # Copy script to test system
    remote_fname = '/tmp/%s' % os.path.basename(fname)
    ansible_runner.copy(src=fname, dest=remote_fname, mode='0755')

    # Run awx-manage inventory_import
    contacted = ansible_runner.shell(
        "awx-manage inventory_import --inventory-name %s --source %s"
        % (inventory.name, remote_fname)
    )

    # Verify the import completed successfully
    for result in contacted.values():
        assert result['rc'] == 0, \
            "awx-manage inventory_import failed: %s" % \
            json.dumps(result, indent=2)

    return inventory


@pytest.fixture(
    scope="class",
    params=[
        {'playbook': 'debug-50.yml', 'forks': 25, },
        {'playbook': 'debug-50.yml', 'forks': 50, },
        {'playbook': 'debug-50.yml', 'forks': 100, },
        {'playbook': 'debug-50.yml', 'forks': 200, },
        {'playbook': 'debug-50.yml', 'forks': 400, },
    ]
)
def job_template(request, api_job_templates_pg, inventory, random_project, credential):
    payload = dict(name="template-%s-%s" % (request.param, fauxfactory.gen_utf8()),
                   job_type='run',
                   playbook=request.param['playbook'],
                   job_tags='',
                   limit='',
                   inventory=inventory.id,
                   project=random_project.id,
                   credential=credential.id,
                   allow_callbacks=False,
                   verbosity=0,
                   forks=request.param['forks'])

    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


# For some reason, the following 'mark' causes all subsequent tests to skip as
# well.  Setting 'pytestmark' works around this issue.
# @pytest.mark.performance
pytestmark = [pytest.mark.performance]


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Host_Fork(Base_Api_Test):

    @pytest.mark.usefixtures('authtoken')
    def test_awx_job_launch(self, api_jobs_pg, job_template):
        """1) Launch the job_template
        2) Poll for status
        3) Assert results
        """
        # Create the job
        payload = dict(name=job_template.name,  # Add Date?
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

        # Wait 30mins for job to complete
        job_pg = job_pg.wait_until_completed(timeout=60 * 30)

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback)

        created = datetime.datetime.strptime(job_pg.created, '%Y-%m-%dT%H:%M:%S.%fZ')
        modified = datetime.datetime.strptime(job_pg.modified, '%Y-%m-%dT%H:%M:%S.%fZ')
        delta = modified - created

        # print "playbook:%s, forks:%s, runtime:%s (%s seconds)" % (job_template.playbook, job_template.forks, delta, delta.total_seconds())

        # Now determine when the job_events complete by looking for an event 'playbook_on_stats'
        job_events_pg = job_pg.get_related('job_events', event='playbook_on_stats')
        attempts = 1
        while job_events_pg.count != 1 and attempts < 40:
            # print "job_events (event=playbook_on_stats) found: %s" % job_events_pg.count
            time.sleep(5)
            job_events_pg.get()
            attempts += 1
        assert job_events_pg.count == 1, "job_event 'playbook_on_stats' not found for job:%s" % job_pg.id
        job_event_pg = job_events_pg.results.pop()

        event_completed = datetime.datetime.strptime(job_event_pg.modified, '%Y-%m-%dT%H:%M:%S.%fZ')
        event_delta = event_completed - modified

        self.metrics['tower'].append(dict(playbook=job_template.playbook,
                                          forks=job_template.forks,
                                          runtime=delta.total_seconds(),
                                          event_time=event_delta.total_seconds()))

    def test_ansible_job_launch(self, ansible_runner, inventory, random_project, job_template):

        cmd = "REST_API_URL='http://{username}:{password}@localhost'".format(**self.credentials['default'])
        cmd += " INVENTORY_HOSTVARS=1"
        cmd += " INVENTORY_ID='%s'" % inventory.id
        cmd += " ansible-playbook -i /usr/lib/python2.7/dist-packages/awx/plugins/inventory/awxrest.py" \
               " --forks %s /var/lib/awx/projects/%s/%s" % \
               (job_template.forks, random_project.local_path, job_template.playbook)
        results = ansible_runner.shell(cmd)

        # Convert HH:MM:SS.SSSSS into datetime object
        (hours, minutes, seconds) = results['delta'].split(':')
        delta = datetime.timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))

        # print "playbook:%s, forks:%s, runtime:%s (%s seconds)" % (job_template.playbook, job_template.forks, delta, delta.total_seconds())
        self.metrics['ansible'].append(dict(playbook=job_template.playbook, forks=job_template.forks, runtime=delta.total_seconds()))

    @classmethod
    def setup_class(self):
        super(Test_Host_Fork, self).setup_class()
        self.metrics = dict(tower=[], ansible=[])

    @classmethod
    def teardown_class(self):

        assert 'tower' in self.metrics
        assert 'ansible' in self.metrics
        assert len(self.metrics['tower']) == len(self.metrics['ansible'])

        print
        print "Playbook Performance (%s hosts)" % NUM_HOSTS
        print
        print "%-12s %12s %15s %15s %15s" % ('Playbook', 'Num_Forks', 'Ansible', 'Tower', 'Event_Delay')
        print "%s=%s=%s=%s=%s" % ('=' * 12, '=' * 12, '=' * 15, '=' * 15, '=' * 15)
        for (tower, ansible) in zip(self.metrics['tower'], self.metrics['ansible']):
            assert tower['playbook'] == ansible['playbook']
            assert tower['forks'] == ansible['forks']
            print "%-12s %12s %15.2f %15.2f %15.2f" % \
                (tower['playbook'], tower['forks'], ansible['runtime'], tower['runtime'], tower['event_time'],)
