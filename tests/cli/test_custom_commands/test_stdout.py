import pytest


@pytest.mark.usefixtures('authtoken')
class TestStdoutDownload(object):

    def test_job_stdout(self, cli, job_template_ping):
        job = job_template_ping.launch().wait_until_completed()
        result = cli(['awx', 'jobs', 'stdout', str(job.id)], auth=True)
        for line in job_template_ping.connection.get(
            job.related.stdout,
            query_parameters=dict(format='txt_download')
        ).content.splitlines():
            assert line in result.stdout

    def test_project_update(self, cli, project_ansible_playbooks_git):
        pu = project_ansible_playbooks_git.update().wait_until_completed()
        result = cli(['awx', 'project_updates', 'stdout', str(pu.id)], auth=True)
        for line in project_ansible_playbooks_git.connection.get(
            pu.related.stdout,
            query_parameters=dict(format='txt_download')
        ).content.splitlines():
            assert line in result.stdout

    def test_inventory_update(self, cli, inventory_source):
        iu = inventory_source.update().wait_until_completed()
        result = cli(['awx', 'inventory_updates', 'stdout', str(iu.id)], auth=True)
        for line in inventory_source.connection.get(
            iu.related.stdout,
            query_parameters=dict(format='txt_download')
        ).content.splitlines():
            assert line in result.stdout

    def test_adhoc_stdout(self, cli, ad_hoc_with_status_completed):
        ahc = ad_hoc_with_status_completed
        result = cli(['awx', 'ad_hoc_commands', 'stdout', str(ahc.id)], auth=True)
        for line in ahc.connection.get(
            ahc.related.stdout,
            query_parameters=dict(format='txt_download')
        ).content.splitlines():
            assert line in result.stdout
