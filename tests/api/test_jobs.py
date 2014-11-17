import pytest
import json
import common.tower.inventory
import common.utils
from dateutil.parser import parse as du_parse
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def job_template_proot_1(request, job_template_ansible_playbooks_git, host_local):
    '''
    Return a job_template for running the test_proot.yml playbook.
    '''
    payload = dict(name="playbook:test_proot.yml, random:%s" % (common.utils.random_unicode()),
                   description="test_proot.yml - %s" % (common.utils.random_unicode()),
                   playbook='test_proot.yml')
    return job_template_ansible_playbooks_git.patch(**payload)


@pytest.fixture(scope="function")
def job_template_proot_2(request, organization, api_inventories_pg, api_job_templates_pg, job_template_proot_1):
    '''
    Create a job_template that uses the same playbook as job_template_proot_1,
    but runs against a different inventory. By using a different inventory,
    Tower will run job_template_proot_1 and job_template_proot_2 to run at the
    same time.
    '''
    # create inventory
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=organization.id,)
    inventory = api_inventories_pg.post(payload)
    request.addfinalizer(inventory.delete)

    # create host
    payload = dict(name="local",
                   description="a non-random local host",
                   variables=json.dumps(dict(ansible_ssh_host="127.0.0.1", ansible_connection="local")),
                   inventory=inventory.id,)
    host_local = inventory.get_related('hosts').post(payload)
    request.addfinalizer(host_local.delete)

    # create duplicate job_template
    payload = job_template_proot_1.json
    payload.update(dict(name="playbook:test_proot.yml, random:%s" % (common.utils.random_unicode()),
                        description="test_proot.yml - %s" % (common.utils.random_unicode()),
                        inventory=inventory.id))
    job_template_proot_2 = api_job_templates_pg.post(payload)
    request.addfinalizer(job_template_proot_2.delete)
    return job_template_proot_2


@pytest.fixture(scope="function")
def job_sleep(request, job_template_sleep):
    '''
    Launch the job_template_sleep and return a job resource.
    '''
    return job_template_sleep.launch()


@pytest.fixture(scope="function")
def job_with_status_pending(request, job_sleep):
    '''
    Wait for job_sleep to move from new to queued, and return the job.
    '''
    return job_sleep.wait_until_started()


@pytest.fixture(scope="function")
def job_with_status_running(request, job_sleep):
    '''
    Wait for job_sleep to move from queued to running, and return the job.
    '''
    return job_sleep.wait_until_status('running')


@pytest.fixture()
def utf8_template(request, authtoken, api_job_templates_pg, project_ansible_playbooks_git, host_local, ssh_credential):
    payload = dict(name="playbook:utf-8.yml.yml, random:%s" % (common.utils.random_unicode()),
                   description="utf-8.yml - %s" % (common.utils.random_unicode()),
                   inventory=host_local.inventory,
                   job_type='run',
                   project=project_ansible_playbooks_git.id,
                   credential=ssh_credential.id,
                   playbook='utf-8.yml',)
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_utf8(self, utf8_template):
        '''
        Verify that a playbook full of UTF-8 successfully works through Tower
        '''
        # launch job
        job_pg = utf8_template.launch_job()

        # wait for completion
        job_pg = job_pg.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

    def test_post_as_superuser(self, job_template, api_jobs_pg):
        '''
        Verify a superuser is able to create a job by POSTing to the /api/v1/jobs endpoint.
        '''

        # post a job
        job_pg = api_jobs_pg.post(job_template.json)

        # assert successful post
        assert job_pg.status == 'new'

    def test_post_as_non_superuser(self, non_superusers, user_password, api_jobs_pg, job_template):
        '''
        Verify a non-superuser is unable to create a job by POSTing to the /api/v1/jobs endpoint.
        '''

        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_jobs_pg.post(job_template.json)

    @pytest.mark.skipif(True, reason="not yet implemented")
    def test_relaunch(self):
        '''
        Verify the job->relaunch endpoint behaves as expected
        '''
        assert False

    def test_cancel_pending_job(self, job_with_status_pending):
        '''
        Verify the job->cancel endpoint behaves as expected when canceling a
        pending/queued job
        '''
        cancel_pg = job_with_status_pending.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to cancel
        job_with_status_pending = job_with_status_pending.wait_until_status('canceled')

        assert job_with_status_pending.status == 'canceled', \
            "Unexpected job status after cancelling job (status:%s)" % \
            job_with_status_pending.status

    def test_cancel_running_job(self, job_with_status_running):
        '''
        Verify the job->cancel endpoint behaves as expected when canceling a
        running job
        '''
        cancel_pg = job_with_status_running.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel job (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for job to cancel
        job_with_status_running = job_with_status_running.wait_until_status('canceled')

        assert job_with_status_running.status == 'canceled', \
            "Unexpected job status after cancelling job (status:%s)" % \
            job_with_status_running.status


@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware'])
def job_template_with_cloud_credential(request, job_template, host):
    cloud_credential = request.getfuncargvalue(request.param + '_credential')

    # PATCH the job_template with the correct inventory and cloud_credential
    job_template.patch(inventory=host.inventory,
                       cloud_credential=cloud_credential.id)
    return job_template


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Cloud_Credential_Job(Base_Api_Test):
    '''
    Verify that cloud credentials are properly passed to playbooks as
    environment variables ('job_env')
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_job_env(self, ansible_runner, job_template_with_cloud_credential):
        '''Verify that job_env has the expected cloud_credential variables'''

        # launch job
        job_pg = job_template_with_cloud_credential.launch_job()

        # wait for completion
        job_pg = job_pg.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_pg.is_successful, "Job unsuccessful - %s " % job_pg

        # assert the expected job_env variables are present
        # FIXME: assert the values are correct
        cred = job_pg.get_related('cloud_credential')
        if cred.kind == 'aws':
            required_envvars = ['AWS_ACCESS_KEY', 'AWS_SECRET_KEY']
        elif cred.kind == 'rax':
            required_envvars = ['RAX_USERNAME', 'RAX_API_KEY']
        elif cred.kind == 'gce':
            required_envvars = ['GCE_EMAIL', 'GCE_PROJECT', 'GCE_PEM_FILE_PATH']
        elif cred.kind == 'azure':
            required_envvars = ['AZURE_SUBSCRIPTION_ID', 'AZURE_CERT_PATH']
        elif cred.kind == 'vmware':
            required_envvars = ['VMWARE_HOST', 'VMWARE_USER', 'VMWARE_PASSWORD']
        else:
            raise Exception("Unhandled cloud type: %s" % cred.kind)

        for required in required_envvars:
            assert required in job_pg.job_env, \
                "Missing required %s environment variable (%s) in job_env.\n%s" % \
                (cred.kind, required, json.dumps(job_pg.job_env))


@pytest.fixture(scope="function")
def cloud_inventory_job_template(request, job_template, cloud_group):
    # PATCH the job_template with the correct inventory and cloud_credential
    job_template.patch(inventory=cloud_group.inventory)
    return job_template


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Update_On_Launch(Base_Api_Test):
    '''
    Verify that, when configured, inventory_updates and project_updates are
    initiated on job launch
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_inventory(self, cloud_inventory_job_template, cloud_group):
        '''Verify that an inventory_update is triggered by job launch'''

        # 1) Set update_on_launch
        inv_src_pg = cloud_group.get_related('inventory_source')
        inv_src_pg.patch(update_on_launch=True)
        assert inv_src_pg.update_cache_timeout == 0
        assert inv_src_pg.last_updated is None, "Not expecting inventory_source an have been updated - %s" % json.dumps(inv_src_pg.json, indent=4)

        # 2) Update job_template to cloud inventory
        cloud_inventory_job_template.patch(inventory=cloud_group.inventory)

        # 3) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % json.dumps(inv_src_pg.json, indent=4)

        # 5) Ensure inventory_update was successful
        last_update = inv_src_pg.get_related('last_update')
        assert last_update.is_successful, "last_update unsuccessful - %s" % last_update
        assert inv_src_pg.is_successful, "inventory_source unsuccessful - %s" % json.dumps(inv_src_pg.json, indent=4)

    def test_inventory_multiple(self, job_template, aws_inventory_source, rax_inventory_source):
        '''Verify that multiple inventory_update's are triggered by job launch'''

        # 1) Set update_on_launch
        aws_inventory_source.patch(update_on_launch=True)
        assert aws_inventory_source.update_on_launch
        assert aws_inventory_source.update_cache_timeout == 0
        assert aws_inventory_source.last_updated is None, "Not expecting inventory_source to have been updated - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)
        rax_inventory_source.patch(update_on_launch=True)
        assert rax_inventory_source.update_on_launch
        assert rax_inventory_source.update_cache_timeout == 0
        assert rax_inventory_source.last_updated is None, "Not expecting inventory_source to have been updated - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)

        # 2) Update job_template to cloud inventory
        assert rax_inventory_source.inventory == aws_inventory_source.inventory, "The inventory differs between the two inventory sources"
        job_template.patch(inventory=aws_inventory_source.inventory)

        # 3) Launch job_template and wait for completion
        job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        aws_inventory_source.get()
        assert aws_inventory_source.last_updated is not None, "Expecting value for aws_inventory_source last_updated - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)
        assert aws_inventory_source.last_job_run is not None, "Expecting value for aws_inventory_source last_job_run - %s" % \
            json.dumps(aws_inventory_source.json, indent=4)

        rax_inventory_source.get()
        assert rax_inventory_source.last_updated is not None, "Expecting value for rax_inventory_source last_updated - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)
        assert rax_inventory_source.last_job_run is not None, "Expecting value for rax_inventory_source last_job_run - %s" % \
            json.dumps(rax_inventory_source.json, indent=4)

        # 5) Ensure inventory_update was successful
        last_update = aws_inventory_source.get_related('last_update')
        assert last_update.is_successful, "aws_inventory_source -> last_update unsuccessful - %s" % last_update
        assert aws_inventory_source.is_successful, "inventory_source unsuccessful - %s" % json.dumps(aws_inventory_source.json, indent=4)

        # assert last_update successful
        last_update = rax_inventory_source.get_related('last_update')
        assert last_update.is_successful, "rax_inventory_source -> last_update unsuccessful - %s" % last_update
        assert rax_inventory_source.is_successful, "inventory_source unsuccessful - %s" % json.dumps(rax_inventory_source.json, indent=4)

    def test_inventory_cache_timeout(self, cloud_inventory_job_template, cloud_group):
        '''Verify that an inventory_update is not triggered by job launch if the cache is still valid'''

        # 1) Set update_on_launch and a 5min update_cache_timeout
        inv_src_pg = cloud_group.get_related('inventory_source')
        cache_timeout = 60 * 5
        inv_src_pg.patch(update_on_launch=True, update_cache_timeout=cache_timeout)
        assert inv_src_pg.update_cache_timeout == cache_timeout
        assert inv_src_pg.last_updated is None, "Not expecting inventory_source an have been updated - %s" % json.dumps(inv_src_pg.json, indent=4)

        # 2) Update job_template to cloud inventory
        cloud_inventory_job_template.patch(inventory=cloud_group.inventory)

        # 3) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 4) Ensure inventory_update was triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % json.dumps(inv_src_pg.json, indent=4)
        last_updated = inv_src_pg.last_updated
        last_job_run = inv_src_pg.last_job_run

        # 5) Launch job_template and wait for completion
        cloud_inventory_job_template.launch_job().wait_until_completed(timeout=50 * 10)

        # 6) Ensure inventory_update was *NOT* triggered
        inv_src_pg.get()
        assert inv_src_pg.last_updated == last_updated, "An inventory_update was unexpectedly triggered (last_updated changed)- %s" % \
            json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run == last_job_run, "An inventory_update was unexpectedly triggered (last_job_run changed)- %s" % \
            json.dumps(inv_src_pg.json, indent=4)

    def test_project(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git):
        '''Verify that a project_update is triggered by job launch'''

        # 1) set scm_update_on_launch for the project
        project_ansible_playbooks_git.patch(scm_update_on_launch=True)
        assert project_ansible_playbooks_git.scm_update_on_launch
        assert project_ansible_playbooks_git.scm_update_cache_timeout == 0
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 3) Ensure project_update was triggered and successful
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated != last_updated, \
            "A project_update was not triggered, last_updated (%s) remains unchanged" % last_updated
        assert project_ansible_playbooks_git.is_successful, "project unsuccessful - %s" % \
            json.dumps(project_ansible_playbooks_git.json, indent=4)

    def test_project_cache_timeout(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git):
        '''Verify that a project_update is not triggered when the cache_timeout has not exceeded'''

        # 1) set scm_update_on_launch for the project
        cache_timeout = 60 * 5
        project_ansible_playbooks_git.patch(scm_update_on_launch=True, scm_update_cache_timeout=cache_timeout)
        assert project_ansible_playbooks_git.scm_update_on_launch
        assert project_ansible_playbooks_git.scm_update_cache_timeout == cache_timeout
        assert project_ansible_playbooks_git.last_updated is not None
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 3) Ensure project_update was *NOT* triggered
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated == last_updated, "A project_update happened, but was not expected"

    def test_inventory_and_project(self, project_ansible_playbooks_git, job_template_ansible_playbooks_git, cloud_group):
        '''Verify that a project_update and inventory_update are triggered by job launch'''

        # 1) Set scm_update_on_launch for the project
        project_ansible_playbooks_git.patch(scm_update_on_launch=True)
        assert project_ansible_playbooks_git.scm_update_on_launch
        last_updated = project_ansible_playbooks_git.last_updated

        # 2) Set update_on_launch for the inventory
        inv_src_pg = cloud_group.get_related('inventory_source')
        inv_src_pg.patch(update_on_launch=True)
        assert inv_src_pg.update_on_launch

        # 3) Update job_template to cloud inventory
        job_template_ansible_playbooks_git.patch(inventory=cloud_group.inventory)

        # 4) Launch job_template and wait for completion
        job_template_ansible_playbooks_git.launch_job().wait_until_completed(timeout=50 * 10)

        # 5) Ensure inventory_update was triggered and successful
        inv_src_pg.get()
        assert inv_src_pg.last_updated is not None, "Expecting value for last_updated - %s" % json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.last_job_run is not None, "Expecting value for last_job_run - %s" % json.dumps(inv_src_pg.json, indent=4)
        assert inv_src_pg.is_successful, "inventory_source unsuccessful - %s" % json.dumps(inv_src_pg.json, indent=4)

        # 6) Ensure project_update was triggered
        project_ansible_playbooks_git.get()
        assert project_ansible_playbooks_git.last_updated != last_updated, \
            "project_update was not triggered - %s" % json.dumps(project_ansible_playbooks_git.json, indent=4)
        assert project_ansible_playbooks_git.is_successful, "project unsuccessful - %s" % \
            json.dumps(project_ansible_playbooks_git.json, indent=4)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Proot(Base_Api_Test):
    '''
    Tests to assert correctness while running with AWX_PROOT_ENABLED=True
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited', 'AWX_PROOT_ENABLED')

    def test_job_isolation(self, job_template_proot_1, job_template_proot_2):
        '''
        Launch 2 jobs and verify that they each:
         - complete successfully
         - ran at the same time

        The playbook used is test_proot.yml which attempts to examine
        filesystem resources it should *NOT* have access to when
        AWX_PROOT_ENABLED=True.  For example, it verifies:
         - /var/lib/awx/projects/ - only a single directory exists for the current job
         - /var/lib/awx/job_status/ - no files are present (job status isn't created until after a job completes)
         - /tmp/ansible_tower_* - only a single matching directory exists
         - /etc/awx/settings.py - No such file or directory
         - /var/log/supervisor/* - Permission Denied
        '''
        # launch jobs
        job_proot_1 = job_template_proot_1.launch()
        job_proot_2 = job_template_proot_2.launch()

        # wait for completion
        job_proot_1 = job_proot_1.wait_until_completed(timeout=60 * 10)

        # wait for completion
        job_proot_2 = job_proot_2.wait_until_completed(timeout=60 * 10)

        # assert successful completion of job
        assert job_proot_1.is_successful, "Job unsuccessful - %s " % job_proot_1

        # assert successful completion of job
        assert job_proot_2.is_successful, "Job unsuccessful - %s " % job_proot_2

        # assert that the two jobs ran at the same time
        # assert that job#1 started before job#2 finished
        assert du_parse(job_proot_1.started) < du_parse(job_proot_2.finished), \
            "Job#1 (id:%s) started (%s) after job#2 (id:%s) finished (%s)" % \
            (job_proot_1.id, job_proot_1.started, job_proot_2.id, job_proot_2.finished)

        # assert that job#1 finished after job#2 started
        assert du_parse(job_proot_1.finished) > du_parse(job_proot_2.started), \
            "Job#1 (id:%s) started (%s) after job#2 (id:%s) finished (%s)" % \
            (job_proot_1.id, job_proot_1.finished, job_proot_2.id, job_proot_2.started)
