import logging

from towerkit.tower import license
import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


class LicenseTest(Base_Api_Test):

    REBRANDING_FLAGS = ["CUSTOM_LOGIN_INFO", "CUSTOM_LOGO"]
    ACTIVITY_STREAM_FLAGS = ["ACTIVITY_STREAM_ENABLED", "ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC"]
    ENTERPRISE_AUTH_SERVICES = ['radius', 'ldap', 'saml']

    license_instance_count = 10

    @pytest.fixture
    def legacy_license_json(self):
        return license.generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email())

    @pytest.fixture
    def enterprise_license_json(self):
        return license.generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email(),
                                        license_type="enterprise")

    @pytest.fixture
    def trial_legacy_license_json(self):
        return license.generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        trial=True,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email())

    @pytest.fixture
    def install_legacy_license(self, request, api_config_pg, legacy_license_json):
        # Apply license
        log.debug("calling fixture install_legacy_license")
        api_config_pg.post(legacy_license_json)
        request.addfinalizer(api_config_pg.delete)

        # Confirm that license is present
        conf = api_config_pg.get()
        assert conf.is_valid_license, 'Expected valid license, invalid license found'

        # Confirm license type, license_key have expected values
        assert conf.is_legacy_license, \
            "Expected legacy license, found %s." % conf.license_info.license_type
        assert conf.license_info.license_key == legacy_license_json['license_key'], \
            "License found differs from license applied"

    @pytest.fixture
    def install_trial_legacy_license(self, request, api_config_pg):
        log.debug("calling fixture install_trial_legacy_license")
        license_info = license.generate_license(instance_count=self.license_instance_count, days=31, trial=True)
        api_config_pg.post(license_info)
        request.addfinalizer(api_config_pg.delete)

        # Confirm that license is present
        conf = api_config_pg.get()
        assert conf.is_valid_license, 'Expected valid license, invalid license found'

        # Confirm license type, license_key have expected values
        assert conf.is_legacy_license, \
            "Expected legacy license, found %s." % conf.license_info.license_type
        assert conf.is_trial_license, \
            "Expected trial license, found regular license"
        assert conf.license_info.license_key == license_info['license_key'], \
            "License found differs from license applied"

    @pytest.fixture
    def install_basic_license(self, request, api_config_pg):
        log.debug("calling fixture install_basic_license")
        license_info = license.generate_license(instance_count=self.license_instance_count,
                                                days=31, license_type="basic")
        api_config_pg.post(license_info)
        request.addfinalizer(api_config_pg.delete)

        # Confirm that license is present
        conf = api_config_pg.get()
        assert conf.is_valid_license, 'Expected valid license, invalid license found'

        # Confirm license type, license_key have expected values
        assert conf.is_basic_license, \
            "Expected basic license, found %s." % conf.license_info.license_type
        assert conf.license_info.license_key == license_info['license_key'], \
            "License found differs from license applied"

    @pytest.fixture
    def install_enterprise_license(self, request, api_config_pg, enterprise_license_json):
        log.debug("calling license fixture install_enterprise_license")
        api_config_pg.post(enterprise_license_json)
        request.addfinalizer(api_config_pg.delete)

        # Confirm that license is present
        conf = api_config_pg.get()
        assert conf.is_valid_license, 'Expected valid license, invalid license found'

        # Confirm license type, license_key have expected values
        assert conf.is_enterprise_license, \
            "Expected enterprise license, %s." % conf.license_info.license_type
        assert conf.license_info.license_key == enterprise_license_json['license_key'], \
            "License found differs from license applied"

    @pytest.fixture
    def install_enterprise_license_expired(self, request, api_config_pg):
        log.debug("calling fixture install_enterprise_license_expired")
        license_info = license.generate_license(license_type='enterprise', instance_count=self.license_instance_count,
                                                days=-61)
        api_config_pg.post(license_info)
        request.addfinalizer(api_config_pg.delete)

    @pytest.fixture
    def install_legacy_license_warning(self, request, api_config_pg):
        log.debug("calling fixture install_legacy_license_warning")
        license_info = license.generate_license(instance_count=self.license_instance_count, days=1)
        api_config_pg.post(license_info)
        request.addfinalizer(api_config_pg.delete)

    @pytest.yield_fixture
    def install_legacy_license_expired(self, request, api_config_pg):
        log.debug("calling fixture install_legacy_license_expired")

        def apply_license():
            license_info = license.generate_license(instance_count=self.license_instance_count, days=-61)
            api_config_pg.post(license_info)

        apply_license()
        yield apply_license
        api_config_pg.delete()

    @pytest.fixture
    def install_legacy_license_grace_period(self, request, api_config_pg):
        log.debug("calling fixture install_legacy_license_grace_period")
        license_info = license.generate_license(instance_count=self.license_instance_count, days=-1)
        api_config_pg.post(license_info)
        request.addfinalizer(api_config_pg.delete)

    @pytest.fixture
    def inventory_no_free_instances(self, request, authtoken, api_config_pg, api_inventories_pg, organization):
        payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                       description="Random inventory - %s" % fauxfactory.gen_utf8(),
                       organization=organization.id,)
        obj = api_inventories_pg.post(payload)
        request.addfinalizer(obj.delete)

        # Ensure there are at least 5 active hosts
        hosts_pg = obj.get_related('hosts')
        while api_config_pg.get().license_info.instance_count < 5:
            payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                           inventory=obj.id)
            hosts_pg.post(payload)

        # Install a license with instance_count=3
        license_pl = license.generate_license(instance_count=3,
                                              days=-1,
                                              trial=False,
                                              company_name=fauxfactory.gen_utf8(),
                                              contact_name=fauxfactory.gen_utf8(),
                                              contact_email=fauxfactory.gen_email())
        api_config_pg.post(license_pl)
        request.addfinalizer(api_config_pg.delete)

        return obj

    def assert_instance_counts(self, request, config, hosts, group):
        """Verify hosts can be added up to the provided 'license_instance_count' variable"""
        group_hosts = group.related.hosts.get()

        config.get()

        current_hosts = config.license_info.current_instances

        while current_hosts < self.license_instance_count:
            payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                           description="host-%s" % fauxfactory.gen_utf8(),
                           inventory=group.inventory)

            assert config.license_info.current_instances == current_hosts
            assert config.license_info.free_instances == self.license_instance_count - current_hosts
            assert config.license_info.available_instances == self.license_instance_count

            log.debug("current_instances: {0.license_info.current_instances}, free_instances: "
                      "{0.license_info.free_instances}, available_instances: {0.license_info.available_instances}"
                      .format(config))

            host = group_hosts.post(payload)
            request.addfinalizer(host.silent_delete)

            current_hosts += 1
            config.get()

        host_payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                            description="host-%s" % fauxfactory.gen_utf8(),
                            inventory=group.inventory)

        with pytest.raises(exc.LicenseExceeded):
            group_hosts.post(host_payload)
        with pytest.raises(exc.LicenseExceeded):
            hosts.post(host_payload)

        assert current_hosts == self.license_instance_count
        assert config.license_info.current_instances == self.license_instance_count
        assert config.license_info.free_instances == 0
        assert config.license_info.available_instances == self.license_instance_count

    @pytest.mark.ha_tower
    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        """Verify that hosts can be added up to the 'license_instance_count'"""
        license_info = api_config_pg.get().license_info
        if not license_info:
            pytest.skip("Skipping test because no license is installed.")

        if license_info.date_expired:
            pytest.skip("Skipping test because license is expired.")

        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)
