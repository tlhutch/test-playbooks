import pytest
import json
import fauxfactory
from dateutil.parser import parse as du_parse
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def job_template_proot_1(request, job_template_ansible_playbooks_git, host_local):
    '''
    Return a job_template for running the test_proot.yml playbook.
    '''
    payload = dict(name="playbook:test_proot.yml, random:%s" % (fauxfactory.gen_utf8()),
                   description="test_proot.yml - %s" % (fauxfactory.gen_utf8()),
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
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Random inventory - %s" % fauxfactory.gen_utf8(),
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
    payload.update(dict(name="playbook:test_proot.yml, random:%s" % (fauxfactory.gen_utf8()),
                        description="test_proot.yml - %s" % (fauxfactory.gen_utf8()),
                        inventory=inventory.id))
    job_template_proot_2 = api_job_templates_pg.post(payload)
    request.addfinalizer(job_template_proot_2.delete)
    return job_template_proot_2


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Proot(Base_Api_Test):
    '''
    Tests to assert correctness while running with AWX_PROOT_ENABLED=True
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_unlimited', 'AWX_PROOT_ENABLED')

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
        job_proot_1 = job_proot_1.wait_until_completed(timeout=60 * 2)

        # wait for completion
        job_proot_2 = job_proot_2.wait_until_completed(timeout=60 * 2)

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
            "Job#1 (id:%s) finished (%s) before job#2 (id:%s) started (%s)" % \
            (job_proot_1.id, job_proot_1.finished, job_proot_2.id, job_proot_2.started)

    @pytest.mark.fixture_args(source_script='''#!/usr/bin/env python
import os
import json
import re

errors = list()

# assert that only one ansible_tower_XXXXX tempfile is visible
for tmpdir in ('/tmp', '/var/tmp'):
    for files in os.listdir(tmpdir):
        matches = [f for f in files if re.search(r'^ansible_tower_', f)]
        if matches:
            files = map(lambda f: os.path.join(tmpdir, f), files)
            errors.append(("Tower temporary files", files))

# assert that no project directories are visible
for tower_projects_dir in ('/var/lib/awx/projects', '/var/lib/tower/projects'):
    if not os.path.isdir(tower_projects_dir):
        continue
    files = os.listdir(tower_projects_dir)
    if files:
        files = map(lambda f: os.path.join(tower_projects_dir, f), files)
        errors.append(("Tower project directories", files))

# assert that no job_status files are visible
for tower_job_status_dir in ('/var/lib/awx/job_status', '/var/lib/tower/job_status'):
    if not os.path.isdir(tower_job_status_dir):
        continue
    files = os.listdir(tower_job_status_dir)
    if files:
        files = map(lambda f: os.path.join(tower_job_status_dir, f), files)
        errors.append(("Tower job_status files", files))

# assert that no tower conf files are visible
for tower_conf_dir in ('/etc/awx', '/etc/tower'):
    if not os.path.isdir(tower_conf_dir):
        continue
    files = os.listdir(tower_conf_dir)
    if files:
        files = map(lambda f: os.path.join(tower_conf_dir, f), files)
        errors.append(("Tower config files", files))

# assert that no tower log files are visible
for tower_log_dir in ('/var/log/awx', '/var/log/tower'):
    if not os.path.isdir(tower_log_dir):
        continue
    files = os.listdir(tower_log_dir)
    if files:
        files = map(lambda f: os.path.join(tower_log_dir, f), files)
        errors.append(("Tower log files", files))

if errors:
    err_str = "The following errors were detected while running a proot-enabled inventory_update.\\n"
    for (name, files) in errors:
        err_str += "\\n# %s\\n" % name
        err_str += " - %s" % "\\n - ".join(files)

    raise Exception(err_str)

print json.dumps({})
''')
    def test_inventory_script_isolation(self, api_unified_jobs_pg, custom_inventory_source):
        '''
        Launch a custom inventory_script verify it:
         - completes successfully
         - is unable to view the following directories

        The playbook used is test_proot.yml which attempts to examine
        filesystem resources it should *NOT* have access to when
        AWX_PROOT_ENABLED=True.  For example, it verifies:
         - /var/lib/awx/projects/ - only a single directory exists for the current job
         - /var/lib/awx/job_status/ - no files are present (job status isn't created until after a job completes)
         - /tmp/ansible_tower_* - only a single matching directory exists
         - /etc/awx/settings.py - No such file or directory
         - /var/log/supervisor/* - Permission Denied
        '''

        # TODO - pass tower directories as environment variables
        payload = dict()
        custom_inventory_source.patch(extra_vars=json.dumps(payload))

        # start inventory_update
        job_pg = custom_inventory_source.update()

        # wait for inventory_update to complete
        job_pg = job_pg.wait_until_completed()

        # assert successful inventory_update
        assert job_pg.is_successful, "Inventory update unsuccessful - %s" % job_pg
