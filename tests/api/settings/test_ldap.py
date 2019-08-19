from copy import deepcopy

from awxkit.utils import random_title
from awxkit import config, exceptions
import pytest

from tests.api import APITest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken')
class TestLDAP(APITest):

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

    def create_additional_directory_config(self, dir_number, bind_user):
        new_ldap_settings = dict()
        for k in deepcopy(self.base_ldap_settings):
            if k != 'AUTH_LDAP_BIND_DN':
                new_ldap_settings.update(
                    {"AUTH_LDAP_{}_{}".format(dir_number, k[10:]): self.base_ldap_settings[k]})
        new_ldap_settings.update(
            {'AUTH_LDAP_{}_BIND_DN'.format(dir_number): 'uid={},{}'.format(bind_user, self.user_base_dn)})
        return new_ldap_settings

    def test_ldap_user_creation(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        update_setting_pg(v2.settings.get().get_endpoint('ldap'), self.base_ldap_settings)
        with self.current_user('bbelcher', self.ldap_password):
            bob = v2.me.get().results.pop()
        clean_user_orgs_and_teams(bob)
        assert bob.first_name == 'Bob'
        assert bob.last_name == 'Belcher'
        assert bob.related.organizations.get().count == 0
        assert bob.related.teams.get().count == 0

    @pytest.mark.parametrize('flag', ['is_superuser', 'is_system_auditor'])
    def test_ldap_user_flag_permissions(self, v2, update_setting_pg, clean_user_orgs_and_teams, flag):
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_USER_FLAGS_BY_GROUP'] = {flag: [
            'cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
            'cn=planetexpress_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com']}
        update_setting_pg(v2.settings.get().get_endpoint(
            'ldap'), ldap_settings)
        matching_users = ['hfarnsworth', 'libelcher']
        for u in matching_users:
            with self.current_user(u, self.ldap_password):
                superuser = v2.me.get().results.pop()
                assert getattr(superuser, flag) is True
        [clean_user_orgs_and_teams(v2.users.get(username=u).results.pop()) for u in matching_users]

    def test_ldap_is_superuser_supercedes_is_auditor(self, v2, update_setting_pg, clean_user_orgs_and_teams, resource_with_schedule):
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_USER_FLAGS_BY_GROUP'] = {'is_superuser': ['cn=planetexpress_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'],
                                                          'is_auditor': ['cn=planetexpress_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com']}
        update_setting_pg(v2.settings.get().get_endpoint(
            'ldap'), ldap_settings)
        with self.current_user('hfarnsworth', self.ldap_password):
            schedule = resource_with_schedule.related.schedules.get(not__name='Cleanup Job Schedule').results.pop()
            schedule.put()
            schedule.patch()
            schedule.delete()
        clean_user_orgs_and_teams('hfarnsworth')

    def test_ldap_organization_creation_and_user_sourcing(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        org_name = 'LDAP_Organization_{}'.format(random_title())
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_ORGANIZATION_MAP'] = {
            org_name: dict(admins='cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
                           auditors='cn=bobsburgers_admins,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com',
                           users=['cn=bobsburgers,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'],
                           remove_admins=False, remove_auditors=False, remove_users=True)
        }

        update_setting_pg(v2.settings.get().get_endpoint('ldap'), ldap_settings)
        assert v2.organizations.get(name=org_name).count == 0
        with self.current_user('libelcher', self.ldap_password):
            linda = v2.me.get().results.pop()
        clean_user_orgs_and_teams(linda)
        org = v2.organizations.get(name=org_name).results.pop()
        users = org.related.users.get()
        assert users.count == 1
        assert users.results.pop().id == linda.id
        admins = org.related.admins.get()
        assert admins.count == 1
        assert admins.results.pop().id == linda.id
        auditor_role = org.get_object_role('Auditor', True)
        auditors = auditor_role.related.users.get()
        assert auditors.count == 1
        assert auditors.results.pop().id == linda.id

    def test_ldap_team_creation_and_user_sourcing(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        org_name = 'Bobs Burgers {}'.format(random_title())
        team_name = 'Bobs Burgers Admin Club {}'.format(random_title())
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
        update_setting_pg(
            v2.settings.get().get_endpoint('ldap'), ldap_settings)
        assert v2.teams.get(name=team_name).count == 0
        with self.current_user('libelcher', self.ldap_password):
            linda = v2.me.get().results.pop()
        clean_user_orgs_and_teams(linda)
        team = v2.teams.get(name=team_name).results.pop()
        users = team.related.users.get()
        assert users.count == 1
        assert users.results.pop().id == linda.id

    def test_ldap_field_truncation(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        """ Verifies that excessively long user attr map values are truncated to 30 characters
            This test assumes that bstrickland has the following value in its initials field
            ohwowthisisasuperlongstringyoumusthaveareallylongname
            """
        ldap_settings = deepcopy(self.base_ldap_settings)
        ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = {'first_name': 'initials',
                                                    'last_name': 'sn',
                                                    'email': 'mail'}
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        update_setting_pg(ldap_endpoint, ldap_settings)
        with self.current_user('bstrickland', self.ldap_password):
            buck = v2.me.get().results.pop()
        clean_user_orgs_and_teams(buck)
        assert buck.first_name == 'ohwowthisisasuperlongstringyou'

    def test_multi_ldap_user_in_second_directory_can_authenticate(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        # Required because of a known issue with multiple directories.
        # This inserts a default configuration with a deliberately broken query.
        # This doesn't cause an error, it just causes the queries to return nothing.
        default_ldap_settings['AUTH_LDAP_USER_SEARCH'] = [
            'cn=lusers,cn=accounts,dc=testing,dc=ansible,dc=com',
            'SCOPE_SUBTREE',
            '(uid=%(user)s)']
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        ldap_settings = [self.create_additional_directory_config(n, u) for n, u in [('1', 'tower_0'),
                                                                                    ('2', 'tower_1')]]
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        [update_setting_pg(ldap_endpoint, s)
         for s in ldap_settings]
        # sarcher is only readable by the tower_1 user
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        clean_user_orgs_and_teams(sterling)
        assert sterling.first_name == 'Sterling'
        assert sterling.last_name == 'Archer'
        assert sterling.related.organizations.get().count == 0
        assert sterling.related.teams.get().count == 0

    def test_multi_ldap_user_can_authenticate_after_error_in_earlier_directory(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        '''In the event that an eariler directory becomes unavailable,
           continue to attempt authenticating the user on other directories.'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_BIND_PASSWORD'] = 'Borked'
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        ldap_settings = [self.create_additional_directory_config(n, u) for n, u in [('1', 'tower_0'),
                                                                                    ('2', 'tower_1')]]
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        [update_setting_pg(ldap_endpoint, s)
         for s in ldap_settings]
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        clean_user_orgs_and_teams(sterling)
        assert sterling.first_name == 'Sterling'
        assert sterling.last_name == 'Archer'
        assert sterling.related.organizations.get().count == 0
        assert sterling.related.teams.get().count == 0

    def test_ldap_user_attributes_are_changed_if_config_updated(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        '''If the attribute map changes, make sure new values
           are set on existing user accts on login'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = {'first_name': 'foo',
                                                            'last_name': 'bar',
                                                            'email': 'bin'}
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        clean_user_orgs_and_teams(sterling)
        assert sterling.first_name == ''
        assert sterling.last_name == ''
        default_ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = self.base_ldap_settings['AUTH_LDAP_USER_ATTR_MAP']
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        assert sterling.first_name == 'Sterling'
        assert sterling.last_name == 'Archer'

    def test_ldap_user_does_not_get_created_if_group_search_is_misconfigured(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        '''if the LDAP directory is configured with the wrong attributes,
           don't create the user'''
        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_GROUP_SEARCH'] = []
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')

        update_setting_pg(ldap_endpoint, default_ldap_settings)

        # Try a login with the "bad" configuration
        with self.current_user('sarcher', self.ldap_password):
            with pytest.raises(exceptions.Unauthorized) as e:
                v2.me.get()
                assert e == "Unauthorized: {u'detail': u'Authentication credentials were not provided. To establish a login session, visit /api/login/.'}"
        bad_config_count = len(v2.users.get(username='sarcher').results)

        # Fix the configuration
        default_ldap_settings['AUTH_LDAP_GROUP_SEARCH'] = self.base_ldap_settings['AUTH_LDAP_GROUP_SEARCH']
        update_setting_pg(ldap_endpoint, default_ldap_settings)

        # Try a login with a "good" configuration
        with self.current_user('sarcher', self.ldap_password):
            try:
                sterling_valid_login = v2.me.get().results.pop()
            except:
                pass
        good_config_count = len(v2.users.get(username='sarcher').results)

        try:
            sterling = v2.users.get(username='sarcher').results.pop()
            clean_user_orgs_and_teams(sterling)
        except NameError:
            pass
        assert bad_config_count == 0
        assert good_config_count == 1
        assert sterling_valid_login

    def test_multi_ldap_first_match_wins(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        '''This test verifies that the user is sourced from the earliest
           directory in which they are found'''

        default_ldap_settings = deepcopy(self.base_ldap_settings)
        # Flipping the first and last name to distinguish which config is used
        default_ldap_settings['AUTH_LDAP_USER_ATTR_MAP'] = {'first_name': 'sn',
                                                            'last_name': 'givenName',
                                                            'email': 'mail'}
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        # tower_1 is the user that can read the sarcher account
        dir1_settings = self.create_additional_directory_config('1', 'tower_1')
        update_setting_pg(ldap_endpoint, dir1_settings)
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        clean_user_orgs_and_teams(sterling)
        assert sterling.first_name == 'Archer'
        assert sterling.last_name == 'Sterling'
        assert sterling.related.organizations.get().count == 0
        assert sterling.related.teams.get().count == 0

    def test_multi_ldap_disallowed_user_in_earlier_directory_can_auth(self, v2, update_setting_pg, clean_user_orgs_and_teams):
        '''This test verifies that a user who is present in the AUTH_LDAP_DENY_GROUP for an earlier
           directory configuration can still authenticate if they are authorized in a later one'''

        default_ldap_settings = deepcopy(self.base_ldap_settings)
        default_ldap_settings['AUTH_LDAP_DENY_GROUP'] = 'cn=dreamland,cn=groups,cn=accounts,dc=testing,dc=ansible,dc=com'
        ldap_endpoint = v2.settings.get().get_endpoint('ldap')
        update_setting_pg(ldap_endpoint, default_ldap_settings)
        # tower_1 is the user that can read the sarcher account
        dir1_settings = self.create_additional_directory_config('1', 'tower_1')
        update_setting_pg(ldap_endpoint, dir1_settings)
        with self.current_user('sarcher', self.ldap_password):
            sterling = v2.me.get().results.pop()
        clean_user_orgs_and_teams(sterling)
        assert sterling.first_name == 'Sterling'
        assert sterling.last_name == 'Archer'
        assert sterling.related.organizations.get().count == 0
        assert sterling.related.teams.get().count == 0
