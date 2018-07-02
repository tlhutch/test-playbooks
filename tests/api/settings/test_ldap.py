from copy import deepcopy

from towerkit.utils import random_title
from towerkit import config
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.ldap
@pytest.mark.mp_group('LDAP', 'isolated_serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestLDAP(Base_Api_Test):

    ldap_password = config.credentials.freeipa.ldap_password
    user_base_dn = 'cn=users,cn=accounts,dc=testing,dc=ansible,dc=com'
    base_ldap_settings = dict(
        AUTH_LDAP_SERVER_URI='ldap://idp.testing.ansible.com',
        AUTH_LDAP_BIND_DN='uid=tower_all,%s' % user_base_dn,
        AUTH_LDAP_BIND_PASSWORD=ldap_password,
        AUTH_LDAP_USER_SEARCH=[
            'cn=users,cn=accounts,dc=testing,dc=ansible,dc=com',
            'SCOPE_SUBTREE',
            '(uid=%(user)s)'
        ],
        AUTH_LDAP_USER_DN_TEMPLATE='',
        AUTH_LDAP_USER_ATTR_MAP=dict(
            first_name='givenName', last_name='sn', email='mail'),
        AUTH_LDAP_GROUP_SEARCH=[
            'cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
            'SCOPE_SUBTREE',
            '(objectClass=posixGroup)'
        ],
        AUTH_LDAP_GROUP_TYPE='MemberDNGroupType',
        AUTH_LDAP_REQUIRE_GROUP=None,
        AUTH_LDAP_DENY_GROUP=None,
        AUTH_LDAP_USER_FLAGS_BY_GROUP={}
    )

    def create_additional_directory_config(self, dir_number, bind_user):
        new_ldap_settings = dict()
        for k in deepcopy(self.base_ldap_settings):
            if k != 'AUTH_LDAP_BIND_DN':
                new_ldap_settings.update(
                    {"AUTH_{}_{}".format(dir_number, k[5:]): self.base_ldap_settings[k]})
        new_ldap_settings.update(
            {'AUTH_{}_LDAP_BIND_DN'.format(dir_number): 'uid={},{}'.format(bind_user, self.user_base_dn)})
        return new_ldap_settings

    def test_ldap_user_creation(self, v2, api_settings_ldap_pg, update_setting_pg):
        update_setting_pg(api_settings_ldap_pg, self.base_ldap_settings)
        with self.current_user('bbelcher', self.ldap_password):
            bob = v2.me.get().results.pop()
            assert bob.first_name == 'Bob'
            assert bob.last_name == 'Belcher'
            assert bob.related.organizations.get().count == 0
            assert bob.related.teams.get().count == 0
        bob.delete()

    def test_ldap_organization_creation_and_user_sourcing(self, v2, api_settings_ldap_pg, update_setting_pg):
        org_name = u'LDAP_Organization_{}'.format(random_title())
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_ORGANIZATION_MAP'] = {
            org_name: dict(admins='cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
                           users=['cn=bobsburgers,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'],
                           remove_admins=False, remove_users=True)
        }
        update_setting_pg(api_settings_ldap_pg, ldap_settings)
        assert v2.organizations.get(name=org_name).count == 0
        with self.current_user('libelcher', self.ldap_password):
            linda = v2.me.get().results.pop()
            org = v2.organizations.get(name=org_name).results.pop()
            users = org.related.users.get()
            assert users.count == 1
            assert users.results.pop().id == linda.id
            admins = org.related.admins.get()
            assert admins.count == 1
            assert admins.results.pop().id == linda.id
        linda.delete()
        org.delete()

    def test_ldap_team_creation_and_user_sourcing(self, v2, api_settings_ldap_pg, update_setting_pg):
        org_name = u'Bobs Burgers {}'.format(random_title())
        team_name = u'Bobs Burgers Admin Club {}'.format(random_title())
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_ORGANIZATION_MAP'] = {
            org_name: dict(admins='cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
                           users=['cn=bobsburgers,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'],
                           remove_admins=False, remove_users=True)
        }
        ldap_settings['AUTH_LDAP_TEAM_MAP'] = {
            team_name: dict(organization=org_name,
                            users=['cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'],
                            remove=True)
        }
        update_setting_pg(api_settings_ldap_pg, ldap_settings)
        assert v2.teams.get(name=team_name).count == 0
        with self.current_user('libelcher', self.ldap_password):
            linda = v2.me.get().results.pop()
            org = v2.organizations.get(name=org_name).results.pop()
            team = v2.teams.get(name=team_name).results.pop()
            users = team.related.users.get()
            assert users.count == 1
            assert users.results.pop().id == linda.id
        linda.delete()
        team.delete()
        org.delete()
