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
            raise Exception("Unhandled cloud type: %s" % request.param)

        for required in required_envvars:
            assert required in job_pg.job_env, \
                "Missing required %s environment variable (%s) in job_env.\n%s" % \
                (cred.kind, required, json.dumps(job_pg.job_env))

@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Update_On_Launch(Base_Api_Test):
    '''
    Verify that, when configured, inventory_updates and project_updates are
    initiated on job launch
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    def test_inventory(self, ansible_runner, job_template, cloud_group):
        '''Verify that an inventory_update is triggered by job launch'''
        pytest.skip("FIXME - Not implemented yet")

    def test_inventory_cache_timeout(self, ansible_runner, job_template, cloud_group):
        '''Verify that an inventory_update is not triggered by job launch if the cache is still valid'''
        pytest.skip("FIXME - Not implemented yet")

    def test_project(self, ansible_runner, job_template, cloud_group):
        '''Verify that a project_update is triggered by job launch'''
        pytest.skip("FIXME - Not implemented yet")

    def test_project_and_inventory(self, ansible_runner, job_template, cloud_group):
        '''Verify that a project_update and inventory_update is triggered by job launch'''
        pytest.skip("FIXME - Not implemented yet")
