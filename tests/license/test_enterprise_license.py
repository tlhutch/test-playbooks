import json

import fauxfactory
import pytest

from tests.lib.tower.license import generate_license
from awxkit.awx.inventory import upload_inventory
from awxkit.exceptions import LicenseExceeded

from tests.license.license import LicenseTest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
class TestEnterpriseLicense(LicenseTest):

    def test_enterprise_license_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print(json.dumps(conf.json, indent=4))

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert NOT AWS
        assert not conf.is_aws_license

        # Assert the license is valid
        assert conf.is_valid_license

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

        # Assess license type
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {'surveys': True,
                            'multiple_organizations': True,
                            'activity_streams': True,
                            'ldap': True,
                            'ha': True,
                            'system_tracking': True,
                            'enterprise_auth': True,
                            'rebranding': True,
                            'workflows': True}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for enterprise license: %s." % conf.license_info

    def test_enterprise_license_job_launch(self, factories):
        """Verify that job templates can be launched."""
        job_template = factories.job_template()
        job_template.launch().wait_until_completed()

    def test_enterprise_license_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)

    @pytest.fixture
    def basic_license_json(self):
        return generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email(),
                                        license_type="basic")

    def test_enterprise_license_downgrade_to_basic(self, basic_license_json, api_config_pg):
        """Verify that an enterprise license can get downgraded to a basic license by posting to api_config_pg."""
        # Update the license
        api_config_pg.post(basic_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key

        # Assess license type
        conf = api_config_pg.get()
        assert conf.license_info['license_type'] == 'basic', \
            "Incorrect license_type returned. Expected 'basic,' " \
            "returned %s." % conf.license_info['license_type']

        # Assert license_key is correct
        expected_license_key = basic_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

    def test_enterprise_license_unable_to_change_system_license(self, v2):
        system_settings = v2.settings.get().get_endpoint('system')
        license = system_settings.LICENSE

        system_settings.LICENSE = {}
        system_settings.delete()
        assert system_settings.get().LICENSE == license

    def test_enterprise_license_delete_license(self, api_config_pg):
        """Verify the license_info field is empty after deleting the license"""
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info,
                                                                                               indent=2)


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_expired')
class TestEnterpriseLicenseExpired(LicenseTest):

    def test_enterprise_license_expired_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print(json.dumps(conf.json, indent=4))

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert NOT AWS information
        assert not conf.is_aws_license

        # Assert the license is valid
        assert conf.is_valid_license

        # Assert dates look sane?
        assert conf.license_info.date_expired
        assert conf.license_info.date_warning

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

        # Assess license type
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise' " \
            "returned %s." % conf.license_info['license_type']

    @pytest.mark.fixture_args(days=1000, older_than='5y', granularity='5y')
    def test_enterprise_license_expired_system_job_launch(self, system_job_with_status_completed):
        """Verify that system jobs can be launched"""
        system_job_with_status_completed.assert_successful()

    def test_enterprise_license_expired_import_license_exceeded(self, skip_if_openshift, api_config_pg, ansible_runner, inventory):
        """Verify import succeeds with a non-trial license thats host count is exceeded."""
        enterprise_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=365)
        api_config_pg.post(enterprise_license_1000)
        dest = upload_inventory(ansible_runner, nhosts=2000)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected awx-manage inventory_import failure." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
            assert 'WARNING  Number of licensed instances exceeded' in result['stderr']
            assert 'http://www.ansible.com/renew for license extension information' in result['stderr']

        assert inventory.get_related('groups').count != 0
        assert inventory.get_related('hosts').count == 2000

    def test_enterprise_license_expired_import_license_expired(self, skip_if_openshift, api_config_pg, ansible_runner, inventory):
        """Verify import succeeds with a non-trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(trial_license_1000)
        dest = upload_inventory(ansible_runner, nhosts=100)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected awx-manage inventory_import failure." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
            assert 'WARNING  License expired' in result['stderr']
            assert 'http://www.ansible.com/renew for license extension information' in result['stderr']

        assert inventory.get_related('groups').count != 0
        assert inventory.get_related('hosts').count == 100

    def test_enterprise_license_expired_import_license_exceeded_and_expired(self, skip_if_openshift, api_config_pg, ansible_runner, inventory):
        """Verify import succeeds with a non-trial license that is expired and thats host count is exceeded."""
        enterprise_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(enterprise_license_1000)
        dest = upload_inventory(ansible_runner, nhosts=2000)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected awx-manage inventory_import failure." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
            assert 'WARNING  Number of licensed instances exceeded' in result['stderr']
            assert 'http://www.ansible.com/renew for license extension information' in result['stderr']

        assert inventory.get_related('groups').count != 0
        assert inventory.get_related('hosts').count == 2000

    def test_enterprise_license_expired_project_update_license_expired(self, api_config_pg, factories):
        """Verify project update succeeds with a non-trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(trial_license_1000)
        p1 = factories.project()
        p1_update = p1.update().wait_until_completed()

        assert p1_update.failed is False, 'project failed to update when it should have succeeded'

    def test_enterprise_license_expired_workflow_launch_license_expired(self, api_config_pg, factories):
        """Verify workflow launch succeeds with a non-trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(trial_license_1000)
        wfjt = factories.workflow_job_template()
        wfjt_launch = wfjt.launch().wait_until_completed()

        assert wfjt_launch.failed is False, 'workflow failed to launch when it should have succeeded'

    def test_enterprise_license_expired_job_launch_license_expired(self, api_config_pg, factories):
        """Verify job launch succeeds with a non-trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(trial_license_1000)
        jt = factories.job_template()
        job = jt.launch().wait_until_completed()

        assert job.failed is False, 'job failed to launch when it should have succeeded'

    def test_enterprise_license_expired_inventory_update_license_expired(self, api_config_pg, factories):
        """Verify inventory update succeeds with a non-trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000)
        api_config_pg.post(trial_license_1000)
        org = factories.organization()
        inv = factories.inventory(organization=org)
        inv_script = factories.inventory_script(organization=org, script="""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'ungrouped': {'hosts': ['will_remove_host']},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch1']},
    'switch2': {'hosts': ['host_switch2']},
    'parent_switch1': {'children': ['switch1']},
    'parent_switch2': {'children': ['switch2']},
    'will_remove_group': {'hosts': ['host_2']},
    'parent_group': {'hosts': ['host_1', 'host_2'], 'children': ['child_group', 'child_group2']}
}))""")
        factories.inventory_source(
            inventory=inv,
            overwrite=True,
            source_script=inv_script,
            organization=org
        )
        inv_update = inv.update_inventory_sources()[0].wait_until_completed()
        assert inv_update.failed is False, 'inventory failed to update when it should have succeeded'
        assert 'WARNING  License expired' in inv_update.result_stdout

    def test_enterprise_license_expired_inventory_update_license_expired_trial(self, api_config_pg, v2, factories, is_docker):
        """Verify job launch fails with a trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000, trial=True)
        api_config_pg.post(trial_license_1000)
        org = factories.organization()

        # NOTE: Assigning instance group because of known latency problem in cluster with license application
        org.add_instance_group(self.primary_instance_group(v2))

        inv = factories.inventory(organization=org)
        inv_script = factories.inventory_script(organization=org, script="""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
print(json.dumps({
    '_meta': {'hostvars': {'host_1': {}, 'host_2': {}}},
    'ungrouped': {'hosts': ['will_remove_host']},
    'child_group': {'hosts': ['host_of_child']},
    'child_group2': {'hosts': ['host_of_child']},
    'not_child': {'hosts': ['host_of_not_child']},
    'switch1': {'hosts': ['host_switch1']},
    'switch2': {'hosts': ['host_switch2']},
    'parent_switch1': {'children': ['switch1']},
    'parent_switch2': {'children': ['switch2']},
    'will_remove_group': {'hosts': ['host_2']},
    'parent_group': {'hosts': ['host_1', 'host_2'], 'children': ['child_group', 'child_group2']}
}))""")
        factories.inventory_source(
            inventory=inv,
            overwrite=True,
            source_script=inv_script,
            organization=org
        )

        iu = inv.update_inventory_sources()[0].wait_until_completed()
        assert iu.status == 'failed'
        assert 'License has expired!' in iu.result_stdout

    def test_enterprise_license_job_launch_license_expired_trial(self, api_config_pg, factories):
        """Verify job launch fails with a trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000, trial=True)
        api_config_pg.post(trial_license_1000)
        jt = factories.job_template()
        with pytest.raises(LicenseExceeded) as e:
            jt.launch()

        assert 'detail' in e.value[1], f'Exception is missing expected "detail" key: {e.value[1]}'
        assert e.value[1]['detail'] == 'License has expired.', f'Exception was not caused by expired license: {e.value[1]["detail"]}'

    def test_enterprise_license_workflow_launch_license_expired_trial(self, api_config_pg, factories):
        """Verify workflow launch fails with a trial license that is expired."""
        trial_license_1000 = generate_license(license_type='enterprise', instance_count=1000, days=-1000, trial=True)
        api_config_pg.post(trial_license_1000)
        wfjt = factories.workflow_job_template()
        with pytest.raises(LicenseExceeded) as e:
            wfjt.launch()

        assert 'detail' in e.value[1], f'Exception is missing expected "detail" key: {e.value[1]}'
        assert e.value[1]['detail'] == 'License has expired.', f'Exception was not caused by expired license: {e.value[1]["detail"]}'

    def test_enterprise_license_import_license_exceeded_trial(self, skip_if_openshift, api_config_pg, ansible_runner, inventory):
        """Verify import fails if the number of imported hosts exceeds licensed host allowance and tower is using a trial license."""
        trial_license_1000 = generate_license(license_type='enterprise', trial=True, instance_count=1000, days=365)
        api_config_pg.post(trial_license_1000)
        dest = upload_inventory(ansible_runner, nhosts=2000)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected awx-manage inventory_import success." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
            assert "Number of licensed instances exceeded" in result['stderr']

        assert inventory.get_related('groups').count == 0
        assert inventory.get_related('hosts').count == 0

    def test_enterprise_license_import_license_expired_trial(self, skip_if_openshift, api_config_pg, ansible_runner, inventory):
        """Verify import fails if a trial license is expired"""
        trial_license_1000 = generate_license(license_type='enterprise', trial=True, instance_count=1000, days=-1000, )
        api_config_pg.post(trial_license_1000)
        dest = upload_inventory(ansible_runner, nhosts=100)

        contacted = ansible_runner.shell('awx-manage inventory_import --inventory-id {0} --source {1}'.format(inventory.id, dest))
        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected awx-manage inventory_import success." \
                "\n[stdout]\n%s\n[stderr]\n%s" % (result['stdout'], result['stderr'])
            assert "License expired" in result['stderr']

        assert inventory.get_related('groups').count == 0
        assert inventory.get_related('hosts').count == 0
