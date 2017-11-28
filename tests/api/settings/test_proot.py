import json

from dateutil.parser import parse as du_parse
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
@pytest.mark.mp_group('Proot', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Proot(Base_Api_Test):
    """Tests to assert correctness while running with AWX_PROOT_ENABLED=True"""

    @pytest.mark.requires_single_instance
    def test_job_isolation(self, factories, api_settings_jobs_pg, update_setting_pg):
        """Launch 2 jobs and verify that they each:
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
        """
        # enable proot
        update_setting_pg(api_settings_jobs_pg, dict(AWX_PROOT_ENABLED=True))

        project = factories.v2_project()
        host = factories.v2_host()
        proot_1, proot_2 = [factories.v2_job_template(inventory=host.ds.inventory,
                                                      project=project, playbook='test_proot.yml',
                                                      verbosity=3) for _ in range(2)]

        jobs = [jt.launch() for jt in (proot_1, proot_2)]
        for job in jobs:
            job.wait_until_completed()
            assert job.is_successful

        job_1, job_2 = jobs

        # assert that the two jobs ran at the same time
        # assert that job#1 started before job#2 finished
        assert du_parse(job_1.started) < du_parse(job_2.finished), \
            "Job#1 (id:%s) started (%s) after job#2 (id:%s) finished (%s)" % \
            (job_1.id, job_1.started, job_2.id, job_2.finished)

        # assert that job#1 finished after job#2 started
        assert du_parse(job_1.finished) > du_parse(job_2.started), \
            "Job#1 (id:%s) finished (%s) before job#2 (id:%s) started (%s)" % \
            (job_1.id, job_1.finished, job_2.id, job_2.started)

    @pytest.mark.fixture_args(source_script="""#!/usr/bin/env python
import os
import json
import re

errors = list()

# assert that only one ansible_tower_XXXXX tempfile is visible
for tmpdir in ('/tmp', '/var/tmp'):
    for files in os.listdir(tmpdir):
        matches = [f for f in files if re.search(r'^awx_proot_', f)]
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
""")
    def test_inventory_script_isolation(self, api_unified_jobs_pg, custom_inventory_source, api_settings_jobs_pg,
                                        update_setting_pg):
        """Launch a custom inventory_script verify it:
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
        """
        # enable proot
        payload = dict(AWX_PROOT_ENABLED=True)
        update_setting_pg(api_settings_jobs_pg, payload)

        # TODO - pass tower directories as environment variables
        payload = dict()
        custom_inventory_source.patch(extra_vars=json.dumps(payload))

        # start inventory_update
        job_pg = custom_inventory_source.update()

        # wait for inventory_update to complete
        job_pg = job_pg.wait_until_completed()

        # assert successful inventory_update
        assert job_pg.is_successful, "Inventory update unsuccessful - %s" % job_pg

    def test_ssh_connections(self, job_with_ssh_connection, api_settings_jobs_pg, update_setting_pg):
        """Verify that jobs complete successfully when connecting to inventory
        using the default ansible connection type (e.g. not local).
        """
        payload = dict(AWX_PROOT_ENABLED=True)
        update_setting_pg(api_settings_jobs_pg, payload)

        # wait for completion
        job_with_ssh_connection = job_with_ssh_connection.wait_until_completed(timeout=60 * 2)

        # assert successful completion of job
        assert job_with_ssh_connection.is_successful, "Job unsuccessful - %s " % job_with_ssh_connection
