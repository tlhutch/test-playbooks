from contextlib import contextmanager
import logging

from tests.lib.tower.license import generate_license
import awxkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


log = logging.getLogger(__name__)


class LicenseTest(APITest):

    REBRANDING_FLAGS = ["CUSTOM_LOGIN_INFO", "CUSTOM_LOGO"]
    ACTIVITY_STREAM_FLAGS = ["ACTIVITY_STREAM_ENABLED", "ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC"]
    ENTERPRISE_AUTH_SERVICES = ['radius', 'ldap', 'saml']

    # as discovered in https://github.com/ansible/tower/issues/4086
    # all 10 node instance count licenses are thought to be basic licenses
    license_instance_count = 15
    basic_license_instance_count = 10

    @pytest.fixture()
    def apply_generated_license(self, api):

        @contextmanager
        def _apply_license_info(license_info):
            config = api.current_version.get().config.get()
            initial_info = config.license_info

            try:
                log.info('Applying {} license...'.format(license_info['license_type']))
                config.post(license_info)
                yield

            finally:
                log.info('Restoring initial license.')
                if not initial_info:
                    config.delete()
                else:
                    initial_info['eula_accepted'] = True
                    config.post(initial_info)

        return _apply_license_info

    @pytest.fixture
    def legacy_license_json(self):
        return generate_license(license_type='legacy', instance_count=self.license_instance_count, days=31,
                                        company_name=fauxfactory.gen_utf8(), contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email())

    @pytest.fixture
    def enterprise_license_json(self):
        return generate_license(license_type='enterprise', instance_count=self.license_instance_count, days=31,
                                        company_name=fauxfactory.gen_utf8(), contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email())

    @pytest.fixture
    def trial_legacy_license_json(self):
        return generate_license(license_type='legacy', instance_count=self.license_instance_count, days=31,
                                        company_name=fauxfactory.gen_utf8(), contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email(), trial=True)

    @pytest.fixture(scope='class')
    def install_legacy_license(self, apply_license):
        with apply_license('legacy', days=31, instance_count=self.license_instance_count):
            yield

    @pytest.fixture(scope='class')
    def install_trial_legacy_license(self, apply_license):
        with apply_license('legacy', days=31, instance_count=self.license_instance_count, trial=True):
            yield

    @pytest.fixture(scope='class')
    def install_basic_license(self, apply_license):
        with apply_license('basic', days=31, instance_count=self.basic_license_instance_count):
            yield

    @pytest.fixture
    def func_install_basic_license(self, apply_license):
        with apply_license('basic', days=31, instance_count=self.basic_license_instance_count):
            yield

    @pytest.fixture(scope='class')
    def install_enterprise_license(self, apply_license):
        with apply_license('enterprise', days=31, instance_count=self.license_instance_count):
            yield

    @pytest.fixture(scope='class')
    def install_enterprise_license_expired(self, apply_license, api_config_pg):
        with apply_license(license_type='enterprise', instance_count=self.license_instance_count, days=-61):
            yield

    @pytest.fixture(scope='class')
    def install_legacy_license_warning(self, apply_license):
        with apply_license(license_type='legacy', instance_count=self.license_instance_count, days=1):
            yield

    @pytest.fixture(scope='class')
    def install_legacy_license_expired(self, apply_license):
        with apply_license(license_type='legacy', instance_count=self.license_instance_count, days=-61):
            yield

    @pytest.fixture(scope='class')
    def install_legacy_license_grace_period(self, apply_license):
        with apply_license(license_type='legacy', instance_count=self.license_instance_count, days=-1):
            yield

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
        license_pl = generate_license(instance_count=3,
                                              days=-1,
                                              trial=False,
                                              company_name=fauxfactory.gen_utf8(),
                                              contact_name=fauxfactory.gen_utf8(),
                                              contact_email=fauxfactory.gen_email())
        api_config_pg.post(license_pl)
        request.addfinalizer(api_config_pg.delete)

        return obj

    def assert_instance_counts(self, request, config, hosts, group, is_basic=False):
        """Verify hosts can be added up to the provided 'license_instance_count' variable"""
        group_hosts = group.related.hosts.get()

        config.get()
        expected_instance_count = self.license_instance_count if not is_basic else self.basic_license_instance_count

        current_hosts = config.license_info.current_instances

        while current_hosts < expected_instance_count:
            payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                           description="host-%s" % fauxfactory.gen_utf8(),
                           inventory=group.inventory)

            assert config.license_info.current_instances == current_hosts
            assert config.license_info.free_instances == expected_instance_count - current_hosts
            assert config.license_info.available_instances == expected_instance_count

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

        assert config.license_info.available_instances == expected_instance_count

        if is_basic:
            # if its not basic, we don't block them from exceeding licensed instance count anymore
            # https://github.com/ansible/tower/issues/3550
            with pytest.raises(exc.LicenseExceeded):
                group_hosts.post(host_payload)
            with pytest.raises(exc.LicenseExceeded):
                hosts.post(host_payload)

            assert current_hosts == expected_instance_count
            assert config.license_info.current_instances == expected_instance_count
            assert config.license_info.free_instances == 0
        else:
            group_hosts.post(host_payload)
            host_payload['name'] = f'another-{host_payload["name"]}'
            hosts.post(host_payload)
            config.get()
            assert config.license_info.current_instances > expected_instance_count
            assert config.license_info.free_instances < 0
