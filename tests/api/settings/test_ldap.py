from copy import deepcopy

from towerkit.utils import random_title
from towerkit import config, exceptions
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
        AUTH_LDAP_BIND_DN='uid=tower_all,{}'.format(user_base_dn),
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

    @pytest.fixture
    def ldap_clean_users_orgs_teams(user, request):
        def func(user):
            def teardown():
                [o.delete() for o in user.related.organizations.get().results
                 if o.name != 'Default']
                [t.delete() for t in user.related.teams.get().results]
                user.delete()
            request.addfinalizer(teardown)
        return func

    def create_additional_directory_config(self, dir_number, bind_user):
        new_ldap_settings = dict()
        for k in deepcopy(self.base_ldap_settings):
            if k != 'AUTH_LDAP_BIND_DN':
                new_ldap_settings.update(
                    {"AUTH_LDAP_{}_{}".format(dir_number, k[10:]): self.base_ldap_settings[k]})
        new_ldap_settings.update(
            {'AUTH_LDAP_{}_BIND_DN'.format(dir_number): 'uid={},{}'.format(bind_user, self.user_base_dn)})
        return new_ldap_settings

    def test_ldap_user_creation(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
        update_setting_pg(api_settings_ldap_pg, self.base_ldap_settings)
        with self.current_user('bbelcher', self.ldap_password):
            bob = v2.me.get().results.pop()
            assert bob.first_name == 'Bob'
            assert bob.last_name == 'Belcher'
            assert bob.related.organizations.get().count == 0
            assert bob.related.teams.get().count == 0
        ldap_clean_users_orgs_teams(bob)

    def test_ldap_organization_creation_and_user_sourcing(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
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
        ldap_clean_users_orgs_teams(linda)

    def test_ldap_team_creation_and_user_sourcing(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
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
            team = v2.teams.get(name=team_name).results.pop()
            users = team.related.users.get()
            assert users.count == 1
            assert users.results.pop().id == linda.id
        ldap_clean_users_orgs_teams(linda)

    def test_multi_ldap_user_in_second_directory_can_authenticate(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        # Required because of a known issue with multiple directories.
        # This inserts a default configuration with a deliberately broken query.
        # This doesn't cause an error, it just causes the queries to return nothing.
        default_ldap_settings['AUTH_LDAP_USER_SEARCH'] = [
            'cn=lusers,cn=accounts,dc=testing,dc=ansible,dc=com',
            'SCOPE_SUBTREE',
            '(uid=%(user)s)']
        ldap_settings = [self.create_additional_directory_config(n, u) for n, u in [('1', 'tower_0'),
                                                                                    ('2', 'tower_1')]]
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        [update_setting_pg(api_settings_ldap_pg, s) for s in ldap_settings]
        # sarcher is only readable by the tower_1 user
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
            assert sterling.first_name == 'Sterling'
            assert sterling.last_name == 'Archer'
            assert sterling.related.organizations.get().count == 0
            assert sterling.related.teams.get().count == 0
        ldap_clean_users_orgs_teams(sterling)

    def test_multi_ldap_user_can_authenticate_after_error_in_earlier_directory(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
        '''In the event that an eariler directory becomes unavailable,
            continue to attempt authenticating the user on other directories.'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_BIND_PASSWORD'] = 'Borked'
        ldap_settings = [self.create_additional_directory_config(n, u) for n, u in [('1', 'tower_0'),
                                                                                    ('2', 'tower_1')]]
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        [update_setting_pg(api_settings_ldap_pg, s) for s in ldap_settings]
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
            assert sterling.first_name == 'Sterling'
            assert sterling.last_name == 'Archer'
            assert sterling.related.organizations.get().count == 0
            assert sterling.related.teams.get().count == 0
        ldap_clean_users_orgs_teams(sterling)

    def test_ldap_user_attributes_are_changed_if_config_updated(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
        ''' If the attribute map changes, make sure new values
            are set on existing user accts on login'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = {'first_name':'foo',
                                                            'last_name':'bar',
                                                            'email':'bin'}
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            v2.me.get().results.pop()
        default_ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = self.base_ldap_settings['AUTH_LDAP_USER_ATTR_MAP']
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        ldap_clean_users_orgs_teams(sterling)
        assert sterling.first_name == 'Sterling'
        assert sterling.last_name == 'Archer'


    @pytest.mark.github('https://github.com/ansible/tower/issues/2465')
    def test_ldap_user_does_not_get_created_if_group_search_is_misconfigured(self, v2, api_settings_ldap_pg, update_setting_pg, ldap_clean_users_orgs_teams):
        ''' if the LDAP directory is configured with the wrong attributes,
        don't create the user'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_GROUP_SEARCH'] = []
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            with pytest.raises(exceptions.Unauthorized):
                v2.me.get().results.pop()
        bad_config_count = len(v2.users.get(username='sarcher').results)
        default_ldap_settings['AUTH_LDAP_GROUP_SEARCH'] = self.base_ldap_settings['AUTH_LDAP_GROUP_SEARCH']
        update_setting_pg(api_settings_ldap_pg, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            try:
                sterling_valid_login = False
                sterling_valid_login = v2.me.get().results.pop()
            except:
                pass
        good_config_count = len(v2.users.get(username='sarcher').results)
        try:
            sterling = v2.users.get(username='sarcher').results.pop()
            ldap_clean_users_orgs_teams(sterling)
        except NameError:
            pass
        assert bad_config_count == 0
        assert good_config_count == 0
        assert sterling_valid_login




