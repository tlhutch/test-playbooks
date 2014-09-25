import pytest
import json
import common.tower.inventory
import common.utils
from tests.api import Base_Api_Test


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

    # def test_no_such_playbook(self, utf8_template):


@pytest.fixture(scope="function", params=['aws', 'rax', 'azure', 'gce', 'vmware'])
def cloud_credential(request, aws_credential, rax_credential, azure_credential, gce_credential, vmware_credential):
    if request.param == 'aws':
        return aws_credential
    elif request.param == 'rax':
        return rax_credential
    elif request.param == 'azure':
        return azure_credential
    elif request.param == 'gce':
        return gce_credential
    elif request.param == 'vmware':
        return vmware_credential
    else:
        raise Exception("Unhandled cloud credential type: %s" % request.param)


@pytest.fixture(scope="function")
def job_template_with_cloud_credential(request, job_template, host, cloud_credential):
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
        assert last_update.is_successful, "last_update unsuccessful - %s" % json.dumps(last_update.json, indent=4)
        assert inv_src_pg.is_successful, "inventory_source unsuccessful - %s" % json.dumps(inv_src_pg.json, indent=4)

    def test_inventory_multiple(self, job_template, aws_inventory_source, rax_inventory_source):
        '''Verify that multiple inventory_update are triggered by job launch'''

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
        assert last_update.is_successful, "aws_inventory_source -> last_update unsuccessful - %s" % json.dumps(last_update.json, indent=4)
        assert aws_inventory_source.is_successful, "inventory_source unsuccessful - %s" % json.dumps(aws_inventory_source.json, indent=4)

        # assert last_update successful
        last_update = rax_inventory_source.get_related('last_update')
        assert last_update.is_successful, "rax_inventory_source -> last_update unsuccessful - %s" % json.dumps(last_update.json, indent=4)
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
