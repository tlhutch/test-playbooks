import json

from dateutil.parser import parse as du_parse
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('Proot', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Proot(APITest):
    """Tests to assert correctness while running with AWX_PROOT_ENABLED=True"""

    @pytest.fixture
    def isolated_instance_group(self, v2):
        return v2.instance_groups.get(name='protected').results.pop()

    @pytest.fixture(scope='class', autouse=True)
    def set_proot_true(self, authtoken, api_settings_jobs_pg, update_setting_pg_class):
        # enable proot
        update_setting_pg_class(api_settings_jobs_pg, dict(AWX_PROOT_ENABLED=True))

    def test_isolated_nodes_use_bwrap(self, skip_if_not_traditional_cluster, v2, factories, isolated_instance_group):
        """Test that isolated nodes invoke bwrap when they run jobs.

        Regression test for https://github.com/ansible/tower/issues/3431
        """
        host = factories.host()
        jt = factories.job_template(inventory=host.ds.inventory, playbook='chatty_tasks.yml')
        jt.add_instance_group(isolated_instance_group)
        job = jt.launch()
        job.wait_until_completed().assert_successful()
        assert job.job_args, "We should see what job args were passed"
        assert 'bwrap' in job.job_args, "bwrap should have been in the args but it was not!"

    def test_job_isolation(self, skip_if_cluster, factories):
        """Launch 2 jobs and verify that they each:
         - complete successfully
         - ran at the same time

        The playbook used is test_proot.yml which attempts to examine
        filesystem resources it should *NOT* have access to when
        AWX_PROOT_ENABLED=True.  For example, it verifies:
         - /var/lib/awx/projects/ - only a single directory exists for the current job
         - /var/lib/awx/job_status/ - no files are present (job status isn't created until after a job completes)
         - /tmp/awx_\w*_\w* - only a single matching directory exists (name of dir defined at https://github.com/ansible/awx/blob/f22fd58392eaaf3eeac9c2ee383d276bfecb5af9/awx/main/tasks.py#L701)
         - /etc/awx/settings.py - No such file or directory
         - /var/log/supervisor/* - Permission Denied
        """
        project = factories.project()
        host = factories.host()
        proot_1, proot_2 = [factories.job_template(inventory=host.ds.inventory,
                                                      project=project, playbook='test_proot.yml',
                                                      verbosity=3) for _ in range(2)]

        jobs = [jt.launch() for jt in (proot_1, proot_2)]
        for job in jobs:
            job.wait_until_completed()
            # The playbook itself asserts the proot setting took effect
            job.assert_successful()

        job_1, job_2 = jobs

        # assert that the two jobs ran at the same time
        # assert that job#1 started before job#2 finished
        assert du_parse(job_1.started) < du_parse(job_2.finished), \
            "Job#1 (id:%s) started (%s) after job#2 (id:%s) finished (%s)" % \
            (job_1.id, job_1.started, job_2.id, job_2.finished)

    @pytest.mark.fixture_args(source_script="""#!/usr/bin/env python
import os
import json
import re

errors = list()

# assert that only one awx_\w*_\w* tempfile is visible
# name of dir is defined at https://github.com/ansible/awx/blob/f22fd58392eaaf3eeac9c2ee383d276bfecb5af9/awx/main/tasks.py#L701
awx_tmp_files = []
for tmpdir in ('/tmp', '/var/tmp'):
    for file in os.listdir(tmpdir):
        awx_matches = re.search(r'awx_\w*_\w*', file)
        di_matches = re.search(r'runner_di_\w*', file)
        pi_matches = re.search(r'ansible_runner_pi_\w*', file)
        if awx_matches or di_matches or pi_matches:
            full_path = os.path.join(tmpdir, file)
            awx_tmp_files.append(full_path)

if len(awx_tmp_files) > 1:
    # we would see one file -- the job directory created for this job
    errors.append(("Tower temporary files", awx_tmp_files))

# assert that no project directories are visible
for tower_projects_dir in ('/var/lib/awx/projects', '/var/lib/tower/projects'):
    if not os.path.isdir(tower_projects_dir):
        continue
    files = os.listdir(tower_projects_dir)
    if files:
        files = [os.path.join(tower_projects_dir, f) for f in files]
        errors.append(("Tower project directories", files))

# assert that no job_status files are visible
for tower_job_status_dir in ('/var/lib/awx/job_status', '/var/lib/tower/job_status'):
    if not os.path.isdir(tower_job_status_dir):
        continue
    files = os.listdir(tower_job_status_dir)
    if files:
        files = [os.path.join(tower_job_status_dir, f) for f in files]
        errors.append(("Tower job_status files", files))

# assert that no tower conf files are visible
for tower_conf_dir in ('/etc/awx', '/etc/tower'):
    if not os.path.isdir(tower_conf_dir):
        continue
    files = os.listdir(tower_conf_dir)
    if files:
        files = [os.path.join(tower_conf_dir, f) for f in files]
        errors.append(("Tower config files", files))

# assert that no tower log files are visible
for tower_log_dir in ('/var/log/awx', '/var/log/tower'):
    if not os.path.isdir(tower_log_dir):
        continue
    files = os.listdir(tower_log_dir)
    if files:
        files = [os.path.join(tower_log_dir, f) for f in files]
        errors.append(("Tower log files", files))

if errors:
    err_str = "The following errors were detected while running a proot-enabled inventory_update.\\n"
    for (name, files) in errors:
        err_str += "\\n# %s\\n" % name
        err_str += " - %s" % "\\n - ".join(files)

    raise Exception(err_str)

print(json.dumps({}))
""")
    def test_inventory_script_isolation(self, api_unified_jobs_pg, custom_inventory_source):
        """Launch a custom inventory_script verify it:
         - completes successfully
         - is unable to view the following directories

        The playbook used is test_proot.yml which attempts to examine
        filesystem resources it should *NOT* have access to when
        AWX_PROOT_ENABLED=True.  For example, it verifies:
         - /var/lib/awx/projects/ - only a single directory exists for the current job
         - /var/lib/awx/job_status/ - no files are present (job status isn't created until after a job completes)
         - /tmp/awx_\w*_\w* - only a single matching directory exists (name of dir defined at https://github.com/ansible/awx/blob/f22fd58392eaaf3eeac9c2ee383d276bfecb5af9/awx/main/tasks.py#L701)
         - /etc/awx/settings.py - No such file or directory
         - /var/log/supervisor/* - Permission Denied
        """
        # TODO - pass tower directories as environment variables
        payload = dict()
        custom_inventory_source.patch(extra_vars=json.dumps(payload))

        # start inventory_update
        job_pg = custom_inventory_source.update()

        # wait for inventory_update to complete
        job_pg = job_pg.wait_until_completed()

        # assert successful inventory_update
        job_pg.assert_successful()

    def test_ssh_connections(self, skip_if_openshift, job_with_ssh_connection):
        """Verify that jobs complete successfully when connecting to inventory
        using the default ansible connection type (e.g. not local).
        """
        # wait for completion
        job_with_ssh_connection = job_with_ssh_connection.wait_until_completed(timeout=60 * 2)

        # assert successful completion of job
        job_with_ssh_connection.assert_successful()
