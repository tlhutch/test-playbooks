import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
class TestFactCache(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def assert_updated_facts(self, ansible_facts):
        """Perform basic validation on host details ansible_facts."""
        assert ansible_facts.get().module_setup
        assert 'ansible_processor' in ansible_facts
        assert 'ansible_distribution' in ansible_facts
        assert 'ansible_system' in ansible_facts

    def test_use_fact_cache_with_gather_facts(self, factories):
        """Test a use_fact_cache JT with gather facts."""
        host = factories.v2_host()
        ansible_facts = host.related.ansible_facts.get()
        assert not ansible_facts.json

        jt = factories.v2_job_template(playbook='gather_facts.yml', inventory=host.ds.inventory, use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        self.assert_updated_facts(ansible_facts.get())

    @pytest.mark.requires_single_instance
    def test_use_fact_cache_with_custom_scan_modules(self, request, factories, ansible_runner, encrypted_scm_credential):
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
        self.assert_updated_facts(ansible_facts)
        assert ansible_facts.services['sshd.service']
        assert ansible_facts.packages['ansible-tower']
        assert ansible_facts.insights['system_id'] == machine_id

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7308')
    def test_use_fact_cache_with_unicode_hostname(self, factories):
        host = factories.v2_host(name=fauxfactory.gen_utf8())
        jt = factories.v2_job_template(playbook='gather_facts.yml', inventory=host.ds.inventory, use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)

    def test_use_fact_cache_with_hostname_with_spaces(self, factories):
        host = factories.v2_host(name="hostname with spaces")
        jt = factories.v2_job_template(playbook='gather_facts.yml', inventory=host.ds.inventory, use_fact_cache=True)
        assert jt.launch().wait_until_completed().is_successful

        ansible_facts = host.related.ansible_facts.get()
        self.assert_updated_facts(ansible_facts)
