import pytest

import fauxfactory

from tests.cli.utils import format_error


JOB_STATUSES = ('new', 'pending', 'waiting', 'running')


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestJobLaunch(object):

    def test_job_launch_missing_pk(self, cli):
        result = cli(['awx', 'job_templates', 'launch'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            'too few arguments' in result.stdout or
            'the following arguments are required: id' in result.stdout
        )

    def test_job_launch_incorrect_pk(self, cli):
        result = cli(['awx', 'job_templates', 'launch', '999999'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json['detail'] == 'Not found.'

    def test_successful_job_launch(self, cli, job_template_ping):
        before = job_template_ping.related.jobs.get().count
        result = cli(['awx', 'job_templates', 'launch', str(job_template_ping.id)], auth=True)
        assert result.returncode == 0, format_error(result)
        assert job_template_ping.related.jobs.get().count == before + 1
        related_jobs = job_template_ping.related.jobs.get().results
        assert [job.id for job in related_jobs] == [result.json['id']]
        assert result.json['finished'] is None  # job is running in the background

    @pytest.mark.parametrize('timeout', [None, 1])
    def test_successful_job_launch_and_wait(self, cli, job_template_ping, timeout):
        args = [
            'awx', 'job_templates', 'launch', str(job_template_ping.id),
            '--wait',
        ]
        if timeout:
            args.extend(['--timeout', str(timeout)])
        result = cli(args, auth=True)

        if timeout:
            assert result.returncode == 0, format_error(result)
            assert result.json['status'] in JOB_STATUSES
        else:
            assert result.returncode == 0, format_error(result)
            assert result.json['status'] == 'successful'

    @pytest.mark.parametrize('end_status_and_url', [
        ('successful', 'https://github.com/ansible/test-playbooks'),
        ('failed', 'example.broken.com'),
        ], ids=['successful', 'failed'])
    def test_project_create_and_wait(self, cli, end_status_and_url):
        end_status, url = end_status_and_url
        result, project = cli([
            'awx', 'projects', 'create',
            '--scm_type', 'git',
            '--scm_url', url,
            '--name', fauxfactory.gen_alphanumeric(),
            '--wait',
        ], auth=True, teardown=True, return_page=True)
        assert result.returncode == 0, format_error(result)
        # We expect that the --wait flag made the CLI wait until the first update was completed to return
        assert project.status == end_status
        assert project.scm_url == url

    def test_inventory_update_and_wait(self, cli, custom_inventory_source):
        updates = custom_inventory_source.related.inventory_updates.get()
        assert updates.count == 0
        result = cli([
            'awx',
            'inventory_source',
            'update',
            f'{custom_inventory_source.id}',
            '--wait'
            ], auth=True)
        assert result.returncode == 0, format_error(result)
        # We expect that the --wait flag made the CLI wait until update was completed to return
        updates = custom_inventory_source.related.inventory_updates.get()
        assert updates.count == 1
        this_update = updates.results.pop()
        assert this_update.status == 'successful'

    def test_workflow_command_wait(self, cli, workflow_job_template):
        assert workflow_job_template.related.workflow_jobs.get().count == 0
        result = cli([
            'awx',
            'workflow_job_templates',
            'launch',
            f'{workflow_job_template.id}',
            '--wait'
            ], auth=True)
        assert result.returncode == 0, format_error(result)
        jobs = workflow_job_template.related.workflow_jobs.get()
        assert jobs.count == 1
        job = jobs.results.pop()
        assert job.status == 'successful'

    def test_stdout_monitor(self, cli, job_template_ping):
        result = cli([
            'awx', 'job_templates', 'launch', str(job_template_ping.id),
            '--monitor',
        ], auth=True)
        for marker in (
            '------Starting Standard Out Stream------\n',
            '------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in job_template_ping.connection.get(
            job_template_ping.related.jobs.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line.decode('utf-8') in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestProjectUpdate(object):

    def test_project_update_missing_pk(self, cli):
        result = cli(['awx', 'projects', 'update'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            'too few arguments' in result.stdout or
            'the following arguments are required: id' in result.stdout
        )

    def test_project_update_incorrect_pk(self, cli):
        result = cli(['awx', 'projects', 'update', '999999'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json['detail'] == 'Not found.'

    def test_successful_project_update(self, cli, project_ansible_playbooks_git):
        before = project_ansible_playbooks_git.related.project_updates.get().count
        result = cli([
            'awx', 'projects', 'update',
            str(project_ansible_playbooks_git.id)
        ], auth=True)
        assert result.returncode == 0, format_error(result)
        assert project_ansible_playbooks_git.related.project_updates.get().count == before + 1
        related = project_ansible_playbooks_git.related.project_updates.get().results
        assert result.json['id'] in [pu.id for pu in related]
        assert result.json['finished'] is None  # project update is running in the background

    def test_stdout_monitor(self, cli, project_ansible_playbooks_git):
        result = cli([
            'awx', 'projects', 'update', str(project_ansible_playbooks_git.id),
            '--monitor'
        ], auth=True)
        for marker in (
            '------Starting Standard Out Stream------\n',
            '------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in project_ansible_playbooks_git.connection.get(
            project_ansible_playbooks_git.related.project_updates.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line.decode('utf-8') in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestInventorySourceUpdate(object):

    def test_inventory_source_update_missing_pk(self, cli):
        result = cli(['awx', 'inventory_sources', 'update'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            'too few arguments' in result.stdout or
            'the following arguments are required: id' in result.stdout
        )

    def test_inventory_source_update_incorrect_pk(self, cli):
        result = cli(['awx', 'inventory_sources', 'update', '999999'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json['detail'] == 'Not found.'

    def test_successful_inventory_update(self, cli, inventory_source):
        before = inventory_source.related.inventory_updates.get().count
        result = cli([
            'awx', 'inventory_sources', 'update',
            str(inventory_source.id)
        ], auth=True)
        assert result.returncode == 0, format_error(result)
        assert inventory_source.related.inventory_updates.get().count == before + 1
        related = inventory_source.related.inventory_updates.get().results
        assert result.json['id'] in [iu.id for iu in related]
        assert result.json['finished'] is None  # inventory update is running in the background

    def test_stdout_monitor(self, cli, inventory_source):
        result = cli([
            'awx', 'inventory_sources', 'update', str(inventory_source.id),
            '--monitor'
        ], auth=True)
        for marker in (
            '------Starting Standard Out Stream------\n',
            '------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in inventory_source.connection.get(
            inventory_source.related.inventory_updates.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line.decode('utf-8') in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestAdhocLaunch(object):

    def test_successful_launch(self, v2, cli, host, ssh_credential):
        result = cli([
            'awx', 'ad_hoc_commands', 'create', '--inventory',
            str(host.inventory), '--credential', str(ssh_credential.id),
            '--module_args', 'awx-manage --version'
        ], auth=True)
        assert result.returncode == 0, format_error(result)
        assert result.json['status'] in JOB_STATUSES
        assert v2.ad_hoc_commands.get(
            id=result.json['id']
        ).results[0].module_args == 'awx-manage --version'

    def test_ahc_stdout_monitor(self, v2, cli, host, ssh_credential):
        result = cli([
            'awx', 'ad_hoc_commands', 'create', '--inventory',
            str(host.inventory), '--credential', str(ssh_credential.id),
            '--module_args', 'awx-manage --version',
            '--monitor', '-f', 'jq', '--filter', '.id',
        ], auth=True)
        for marker in (
            '------Starting Standard Out Stream------\n',
            '------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        ahc = v2.ad_hoc_commands.get(
            id=result.stdout.splitlines()[-1]
        ).results[0]
        for line in ahc.connection.get(
            ahc.related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line.decode('utf-8') in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestWorkflowLaunch(object):

    def test_successful_launch(self, v2, cli, factories):
        inv_script = factories.inventory_script()
        inv_source = factories.inventory_source(source_script=inv_script)
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=inv_source)
        result = cli([
            'awx', 'workflow_job_templates', 'launch', str(wfjt.id),
        ], auth=True)
        assert result.returncode == 0, format_error(result)
        assert result.json['status'] in JOB_STATUSES

        wf_jobs = wfjt.related.workflow_jobs.get()
        assert wf_jobs.count == 1
        assert wf_jobs.results[0].id == result.json['id']

    @pytest.mark.parametrize('timeout', [None, 1])
    def test_monitor(self, v2, cli, factories, timeout):
        inv_script = factories.inventory_script()
        inv_source = factories.inventory_source(source_script=inv_script)
        wfjt = factories.workflow_job_template()
        factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=inv_source)
        args = [
            'awx', 'workflow_job_templates', 'launch', str(wfjt.id),
            '--monitor', '-f', 'jq', '--filter', '.status'
        ]
        if timeout:
            args.extend(['--timeout', str(timeout)])
        result = cli(args, auth=True)
        assert result.returncode == 0, format_error(result)
        if timeout:
            assert 'Monitoring aborted due to timeout.' in result.stdout
            assert result.stdout.splitlines()[-1] != 'successful'
        else:
            assert 'Launching'.format(wfjt.name) in result.stdout
            assert ' successful'.format(inv_source.name) in result.stdout
            assert result.stdout.splitlines()[-1] == 'successful'
