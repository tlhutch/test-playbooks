import json

import towerkit.tower
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.fixture()
def num_hosts(request):
    """
    The number of hosts to dynamically create.  The value is used by the
    dynamic_inventory playbook.
    """
    return 50


@pytest.fixture()
def dynamic_inventory(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, host_local, ssh_credential, num_hosts):
    payload = dict(name="playbook:dynamic_inventory.yml, num_hosts:%s, random:%s" % (num_hosts, fauxfactory.gen_utf8()),
                   description="dynamic_inventory, num_hosts:%s" % num_hosts,
                   inventory=host_local.inventory,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   extra_vars=json.dumps(dict(num_hosts=num_hosts)),
                   forks=10,
                   playbook='dynamic_inventory.yml',)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.cleanup)
    return obj


inventory_hosts = [200, 500, 1000, 5000, 10000]


@pytest.fixture(params=inventory_hosts)
def import_inventory(request, authtoken, api_inventories_pg, organization, ansible_runner):
    payload = dict(name="inventory:%s, hosts:%s" % (fauxfactory.gen_alphanumeric(), request.param),
                   description="Random inventory %s with %s hosts" % (fauxfactory.gen_utf8(), request.param),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Upload inventory script
    dest = towerkit.tower.inventory.upload_inventory(ansible_runner, nhosts=request.param)

    # Run awx-manage inventory_import
    contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id %s --source %s' % (obj.id, dest))

    # Verify the import completed successfully
    for result in contacted.values():
        assert result['rc'] == 0, "awx-manage inventory_import failed: %s" \
            % json.dumps(result, indent=2)

    return obj


@pytest.fixture()
def setfact_50(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, import_inventory, ssh_credential):
    num_hosts = import_inventory.get_related('hosts').count
    payload = dict(name="playbook:setfact_50.yml, hosts:%s, random:%s" % (num_hosts, fauxfactory.gen_utf8()),
                   description="setfact_50.yml with %s hosts" % (num_hosts),
                   inventory=import_inventory.id,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   extra_vars=json.dumps(dict(ansible_connection='local')),
                   playbook='setfact_50.yml',)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Events(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_dynamic_inventory(self, dynamic_inventory, num_hosts, tower_version_cmp):
        """
        Verify that the /job_tasks and /job_plays endpoints are correctly
        aggregating data from /job_events
        """

        # Only supported >- tower-2.0.0
        if tower_version_cmp('2.0.0') < 0:
            pytest.xfail("Only supported on tower-2.0.0 (or newer)")

        # launch job
        job_pg = dynamic_inventory.launch_job()

        # wait for completion
        job_pg = job_pg.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_pg.is_completed, "Job unexpectedly still running - %s " % job_pg

        # assert job_plays matches job_events?event=playbook_on_play_start
        job_events_plays = job_pg.get_related('job_events', event='playbook_on_play_start')
        job_plays_pg = job_pg.get_related('job_plays')

        assert job_events_plays.count == job_plays_pg.count, \
            "The /jobs/%s/job_plays endpoint doesn't match the expected " \
            "number of job_events of type 'playbook_on_play_start' (%d != %d)" \
            % (job_pg.id, job_plays_pg.count, job_events_plays.count)

        # assert job_tasks matches job_events?parent=N job_tasks
        for play in job_events_plays.results:

            # NOTE: playbook_on_* events are playbook-scoped and therefore do not have associated tasks.
            # We filter out a subset of these here.
            job_events_tasks = job_pg.get_related('job_events', parent=play.id, not__event__in=','.join(('playbook_on_notify',
                                                                                                         'playbook_on_no_hosts_matched',
                                                                                                         'playbook_on_no_hosts_remaining')))
            job_tasks_pg = job_pg.get_related('job_tasks', event_id=play.id)

            assert job_tasks_pg.count == job_events_tasks.count, \
                "The endpoints /job_tasks and /job_events differ on the " \
                "expected number of tasks for play:%s (%d != %d)" \
                % (play.id, job_tasks_pg.count, job_events_tasks.count)
