import pytest


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestJobLaunch(object):

    def test_job_launch_missing_pk(self, cli):
        result = cli(['awx', 'job_templates', 'launch'], auth=True)
        assert result.returncode == 2
        assert b'the following arguments are required: id' in result.stdout

    def test_job_launch_incorrect_pk(self, cli):
        result = cli(['awx', 'job_templates', 'launch', '999999'], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Not found.'

    def test_successful_job_launch(self, cli, job_template_ping):
        before = job_template_ping.related.jobs.get().count
        result = cli(['awx', 'job_templates', 'launch', str(job_template_ping.id)], auth=True)
        assert result.returncode == 0
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
            assert result.returncode == 0
            assert result.json['status'] in ('new', 'pending', 'running')
        else:
            assert result.returncode == 0
            assert result.json['status'] == 'successful'

    def test_stdout_monitor(self, cli, job_template_ping):
        result = cli([
            'awx', 'job_templates', 'launch', str(job_template_ping.id),
            '--monitor',
        ], auth=True)
        for marker in (
            b'------Starting Standard Out Stream------\n',
            b'------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in job_template_ping.connection.get(
            job_template_ping.related.jobs.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestProjectUpdate(object):

    def test_project_update_missing_pk(self, cli):
        result = cli(['awx', 'projects', 'update'], auth=True)
        assert result.returncode == 2
        assert b'the following arguments are required: id' in result.stdout

    def test_project_update_incorrect_pk(self, cli):
        result = cli(['awx', 'projects', 'update', '999999'], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Not found.'

    def test_successful_project_update(self, cli, project_ansible_playbooks_git):
        before = project_ansible_playbooks_git.related.project_updates.get().count
        result = cli([
            'awx', 'projects', 'update',
            str(project_ansible_playbooks_git.id)
        ], auth=True)
        assert result.returncode == 0
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
            b'------Starting Standard Out Stream------\n',
            b'------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in project_ansible_playbooks_git.connection.get(
            project_ansible_playbooks_git.related.project_updates.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestInventorySourceUpdate(object):

    def test_inventory_source_update_missing_pk(self, cli):
        result = cli(['awx', 'inventory_sources', 'update'], auth=True)
        assert result.returncode == 2
        assert b'the following arguments are required: id' in result.stdout

    def test_inventory_source_update_incorrect_pk(self, cli):
        result = cli(['awx', 'inventory_sources', 'update', '999999'], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Not found.'

    def test_successful_inventory_update(self, cli, inventory_source):
        before = inventory_source.related.inventory_updates.get().count
        result = cli([
            'awx', 'inventory_sources', 'update',
            str(inventory_source.id)
        ], auth=True)
        assert result.returncode == 0
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
            b'------Starting Standard Out Stream------\n',
            b'------End of Standard Out Stream--------\n'
        ):
            assert marker in result.stdout

        # fetch stdout from stdout endpoint
        for line in inventory_source.connection.get(
            inventory_source.related.inventory_updates.get().results[-1].related.stdout,
            query_parameters=dict(format='ansi_download')
        ).content.splitlines():
            assert line in result.stdout


@pytest.mark.usefixtures('authtoken')
class TestAdhocLaunch(object):

    def test_successful_launch(self, v2, cli, host, ssh_credential):
        result = cli([
            'awx', 'ad_hoc_commands', 'create', '--inventory',
            str(host.inventory), '--credential', str(ssh_credential.id),
            '--module_args', 'awx-manage --version'
        ], auth=True)
        assert result.returncode == 0
        assert result.json['status'] in ('new', 'pending', 'running')
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
            b'------Starting Standard Out Stream------\n',
            b'------End of Standard Out Stream--------\n'
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
            assert line in result.stdout


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
        assert result.returncode == 0
        assert result.json['status'] in ('new', 'pending', 'running')

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
        assert result.returncode == 0
        if timeout:
            assert 'Monitoring aborted due to timeout.' in result.stdout.decode('utf-8')
            assert result.stdout.splitlines()[-1] != b'successful'
        else:
            assert 'Launching'.format(wfjt.name) in result.stdout.decode('utf-8')
            assert ' successful'.format(inv_source.name) in result.stdout.decode('utf-8')
            assert result.stdout.splitlines()[-1] == b'successful'
