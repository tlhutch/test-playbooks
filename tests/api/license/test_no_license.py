import json

import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api.license import LicenseTest


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'no_license')
class TestNoLicense(LicenseTest):

    @pytest.fixture
    def missing_eula_legacy_license_json(self, legacy_license_json):
        del legacy_license_json['eula_accepted']
        return legacy_license_json

    @pytest.fixture
    def eula_rejected_legacy_license_json(self, legacy_license_json):
        legacy_license_json['eula_accepted'] = False
        return legacy_license_json

    def test_empty_license_info(self, api_config_pg):
        """Verify the license_info field is empty"""
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info,
                                                                                               indent=4)

    def test_cannot_add_host(self, api_hosts_pg, inventory, group):
        """Verify that no hosts can be added"""
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        with pytest.raises(exc.LicenseExceeded):
            inventory.related.hosts.post(payload)
        with pytest.raises(exc.LicenseExceeded):
            group.related.hosts.post(payload)
        with pytest.raises(exc.LicenseExceeded):
            api_hosts_pg.post(payload)

    def test_can_launch_project_update(self, project_ansible_playbooks_git_nowait):
        """Verify that project_updates can be launched"""
        job_pg = project_ansible_playbooks_git_nowait.update().wait_until_completed()
        assert job_pg.is_successful, "project_update was unsuccessful - %s" % job_pg

    def test_can_launch_inventory_update_but_it_should_fail(self, custom_inventory_source):
        job = custom_inventory_source.update().wait_until_completed()
        assert job.status == 'failed'
        assert 'CommandError: No license found!' in job.result_stdout

    def test_cannot_launch_job(self, install_basic_license, api_config_pg, job_template):
        """Verify that job_templates cannot be launched"""
        api_config_pg.delete()
        with pytest.raises(exc.LicenseExceeded):
            job_template.launch_job()

    @pytest.mark.parametrize('invalid_license_json',
                             [None, 0, 1, -1, True, fauxfactory.gen_utf8(), (), {}, {'eula_accepted': True}])
    def test_post_invalid_license(self, api_config_pg, invalid_license_json):
        """Verify that various bogus license formats fail to successfully install"""
        # Assert expected error when issuing a POST with an invalid license
        if invalid_license_json is not None:
            invalid_license_json = json.dumps(invalid_license_json)

        with pytest.raises(Exception) as e:
            api_config_pg.post(invalid_license_json)

        assert e.type in (exc.LicenseInvalid, exc.BadRequest)

        # Assert that no license has been applied
        conf = api_config_pg.get()
        assert conf.license_info == {}, "No license was expected, found %s" % conf.license_info

    def test_post_legacy_license_without_eula_accepted(self, api_config_pg, missing_eula_legacy_license_json):
        """Verify failure while POSTing a license with no `eula_accepted` attribute."""
        with pytest.raises(exc.LicenseInvalid):
            api_config_pg.post(missing_eula_legacy_license_json)

    def test_post_legacy_license_with_rejected_eula(self, api_config_pg, eula_rejected_legacy_license_json):
        """Verify failure while POSTing a license with `eula_accepted:false` attribute."""
        with pytest.raises(exc.LicenseInvalid):
            api_config_pg.post(eula_rejected_legacy_license_json)

    def test_post_legacy_license(self, api_config_pg, legacy_license_json):
        """Verify that a license can be installed by issuing a POST to the /config endpoint"""
        # Assert that no license present at /api/v1/config/
        conf = api_config_pg.get()
        assert not conf.is_valid_license, "No license was expected, but one was found"

        # Install the license
        api_config_pg.post(legacy_license_json)

        # Assert that license present at /api/v1/config/
        conf = api_config_pg.get()
        assert conf.license_info != {}, "License expected, but none found"
        assert conf.license_info.license_key == legacy_license_json['license_key']
