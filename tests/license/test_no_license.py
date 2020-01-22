import sys
import json

import fauxfactory
import pytest

import awxkit.exceptions as exc
from tests.lib.tower.license import generate_license
from awxkit.utils import poll_until

from tests.license.license import LicenseTest


@pytest.mark.first
@pytest.mark.serial
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

    def test_no_license_cannot_add_host(self, api_hosts_pg, inventory, group):
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

    def test_no_license_can_launch_project_update(self, project_ansible_playbooks_git_nowait):
        """Verify that project_updates can be launched"""
        job_pg = project_ansible_playbooks_git_nowait.update().wait_until_completed()
        job_pg.assert_successful()

    def test_no_license_can_launch_inventory_update_but_it_should_fail(self, custom_inventory_source):
        job = custom_inventory_source.update().wait_until_completed()
        assert job.status == 'failed'
        assert 'CommandError: No license found!' in job.result_stdout

    def test_post_legacy_license_without_eula_accepted(self, api_config_pg, missing_eula_legacy_license_json):
        """Verify failure while POSTing a license with no `eula_accepted` attribute."""
        with pytest.raises(exc.LicenseInvalid):
            api_config_pg.post(missing_eula_legacy_license_json)

    def test_post_legacy_license_with_rejected_eula(self, api_config_pg, eula_rejected_legacy_license_json):
        """Verify failure while POSTing a license with `eula_accepted:false` attribute."""
        with pytest.raises(exc.LicenseInvalid):
            api_config_pg.post(eula_rejected_legacy_license_json)

    @pytest.mark.parametrize('invalid_license_json',
                             [None, 0, 1, -1, True, '<unicode>', (), {}, {'eula_accepted': True}])
    def test_post_invalid_license(self, api_config_pg, invalid_license_json):
        """Verify that various bogus license formats fail to successfully install"""
        # Assert expected error when issuing a POST with an invalid license

        # HACK: pytest chokes when showing debug output that includes a unicode parameter
        if invalid_license_json == '<unicode>':
            invalid_license_json = fauxfactory.gen_utf8()

        if invalid_license_json is not None:
            invalid_license_json = json.dumps(invalid_license_json)

        with pytest.raises(Exception) as e:
            api_config_pg.post(invalid_license_json)

        assert e.type in (exc.LicenseInvalid, exc.BadRequest)

        # Assert that no license has been applied
        conf = api_config_pg.get()
        assert conf.license_info == {}, "No license was expected, found %s" % conf.license_info

    def test_post_legacy_license(self, api_config_pg, legacy_license_json):
        """Verify that a license can be installed by issuing a POST to the /config endpoint"""
        # Assert that no license present at /api/v2/config/
        conf = api_config_pg.get()
        assert not conf.is_valid_license, "No license was expected, but one was found"

        # Install the license
        api_config_pg.post(legacy_license_json)

        # Assert that license present at /api/v2/config/
        conf = api_config_pg.get()
        assert conf.license_info != {}, "License expected, but none found"
        assert conf.license_info.license_key == legacy_license_json['license_key']

    def test_no_license_cannot_launch_job(self, v2, func_install_basic_license, api_config_pg, factories):
        """Verify that job_templates cannot be launched"""
        api_config_pg.delete()
        poll_until(lambda: not v2.config.get().license_info, interval=1, timeout=15)
        job_template = factories.job_template()
        with pytest.raises(exc.LicenseExceeded):
            job_template.launch()

    def test_displayed_system_license(self, api_config_pg, api_settings_system_pg):
        """Verifies that our exact license contents gets displayed under /api/v2/settings/system/.

        Note: the awxkit license generator auto-appends a 'eula_accepted' field which is not
        actually part of the license so we remove that manually below.
        """
        # Installing enterprise license for test_system_license.
        # Put this here because it assumes starting with no license
        license_info = generate_license(
            days=365,
            instance_count=sys.maxsize,
            license_type='enterprise')
        api_config_pg.post(license_info)
        del license_info['eula_accepted']

        # check /api/v2/settings/system/ 'LICENSE' field
        returned_license = api_settings_system_pg.get().json['LICENSE']
        assert license_info == returned_license, \
            "Discrepancy between license and license displayed under /api/v2/settings/system/." \
            "\n\nLicense:\n{0}\n\nAPI returned:\n{1}\n".format(json.dumps(license_info), json.dumps(returned_license))
