import pytest

from awxkit import config
from awxkit import exceptions
from awxkit.api.pages import Subscriptions

from tests.license.license import LicenseTest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'no_license')
class TestRHSMLicense(LicenseTest):

    def test_get_licenses_from_subscription(self, connection):
        subs_page = Subscriptions(connection=connection)
        all_licenses = subs_page.get_possible_licenses(rh_username=config.credentials.redhat.username, rh_password=config.credentials.redhat.password)
        assert len(all_licenses) == 4
        expected_license_names = sorted(['Red Hat Ansible Tower, Premium (Unlimited Managed Nodes, L3 Only)',
            'Ansible Tower by Red Hat, Self-Support (8 Managed Nodes)',
            'Red Hat Ansible Tower, Standard (80639 Managed Nodes, L3 Only)',
            'Ansible Tower by Red Hat, Standard (Managed Hosting Provider)'
            ])
        found_license_names = sorted([sub_license['subscription_name'] for sub_license in all_licenses])
        assert found_license_names == expected_license_names
        for sub_license in all_licenses:
            if 'Unlimited' in sub_license['subscription_name']:
                assert sub_license['instance_count'] == 9999999, sub_license
            if 'Self-Support' in sub_license['subscription_name']:
                assert sub_license['instance_count'] == 8, sub_license
            if '80639 Managed Nodes' in sub_license['subscription_name']:
                assert sub_license['instance_count'] == 80639, sub_license
            if 'Managed Hosting Provider' in sub_license['subscription_name']:
                assert sub_license['instance_count'] == 4, sub_license

    def test_bad_rhsm_password(self, connection):
        subs_page = Subscriptions(connection=connection)
        with pytest.raises(exceptions.BadRequest) as e:
            subs_page.get_possible_licenses(rh_username='bad', rh_password='fake')
        assert "401 Client Error: Unauthorized for url" in str(e.value)

    def test_missing_username_and_password(self, connection):
        subs_page = Subscriptions(connection=connection)
        with pytest.raises(exceptions.BadRequest) as e:
            subs_page.get_possible_licenses()
        assert str(e.value) == "{'error': 'rh_username is required'}"

    def test_apply_licenses_from_subscription(self, connection, apply_license, v2):
        subs_page = Subscriptions(connection=connection)
        all_licenses = subs_page.get_possible_licenses(rh_username=config.credentials.redhat.username, rh_password=config.credentials.redhat.password)
        expected_keys = ['company_name', 'instance_count', 'license_date', 'license_key', 'subscription_name', 'license_type']
        for sub_license in all_licenses:
            sub_license['eula_accepted'] = True
            v2.config.post(sub_license)
            applied_license = v2.config.get()['license_info']
            for key in expected_keys:
                assert key in applied_license.keys()
                assert key in sub_license.keys()
                assert applied_license[key] == sub_license[key]
            v2.config.delete()
