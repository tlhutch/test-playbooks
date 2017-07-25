import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
class TestFactCache(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_launch_with_use_fact_cache_and_gather_facts(self, factories):
        """Test a use_fact_cache JT with gather facts."""
        host = factories.v2_host()
        ansible_facts = host.related.ansible_facts.get()
        assert not ansible_facts.json

        jt = factories.v2_job_template(playbook='gather_facts.yml', inventory=host.ds.inventory, use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        assert ansible_facts.get().module_setup
        assert 'ansible_processor' in ansible_facts
        assert 'ansible_distribution' in ansible_facts
        assert 'ansible_system' in ansible_facts

    @pytest.mark.requires_single_instance
    def test_launch_with_use_fact_cache_and_custom_scan_modules(self, request, factories, ansible_runner, encrypted_scm_credential):
        """Test a use_fact_cache JT with Tower's custom scan modules."""
        host = factories.v2_host()

        machine_id = "4da7d1f8-14f3-4cdc-acd5-a3465a41f25d"
        ansible_runner.file(path='/etc/redhat-access-insights', state="directory")
        ansible_runner.shell('echo -n {0} > /etc/redhat-access-insights/machine-id'.format(machine_id))
        request.addfinalizer(lambda: ansible_runner.file(path='/etc/redhat-access-insights', state="absent"))

        project = factories.v2_project(scm_url="git@github.com:ansible/tower-fact-modules.git",
                                       credential=encrypted_scm_credential, wait=True)
        jt = factories.v2_job_template(project=project, playbook='scan_facts.yml', inventory=host.ds.inventory,
                                       use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        assert 'ansible_processor' in ansible_facts
        assert ansible_facts.insights['system_id'] == machine_id
        assert ansible_facts.services['sshd.service']
        assert ansible_facts.packages['ansible-tower']

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7302')
    def test_clear_facts(self, factories):
        host = factories.v2_host()
        # update project and jt to source jlaska/ansible-playbooks
        project = factories.v2_project(scm_url='https://github.com/simfarm/ansible-playbooks.git',
                                       scm_branch='add_clear_facts_playbook', wait=True)
        jt = factories.v2_job_template(playbook='clear_facts.yml', inventory=host.ds.inventory, project=project,
                                       use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        assert not ansible_facts.get().json
