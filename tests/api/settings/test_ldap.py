import towerkit.exceptions
import pytest

from tests.api import Base_Api_Test


@pytest.fixture(params=["install_legacy_license", "install_enterprise_license"])
def ldap_enabled_license(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(params=["no_license", "install_basic_license"])
def ldap_disabled_license(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture
def cleanup_ldap_info(request, api_users_pg, api_teams_pg, api_organizations_pg):
    def purge_info():
        # Delete Users
        users = api_users_pg.get(username__in=['it_user1', 'eng_admin1'])
        for user in users.results:
            user.delete()

        # Delete team
        teams = api_teams_pg.get(name='LDAP IT')
        for team in teams.results:
            team.delete()

        # Delete organization
        orgs = api_organizations_pg.get(name='LDAP Organization')
        for org in orgs.results:
            org.delete()

    purge_info()
    request.addfinalizer(purge_info)


@pytest.mark.ldap
@pytest.mark.api
@pytest.mark.destructive
class Test_LDAP(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken')

    def test_objects_created_after_successful_login(self, install_legacy_license, cleanup_ldap_info, api_users_pg, user_password):
        """Verify that related LDAP objects are created after a successful
        login. For example, the LDAP User, associated teams and
        organizations.
        """
        # Login as an LDAP user
        with self.current_user(username='it_user1', password=user_password):
            api_users_pg.get(username='it_user1')

        # Verify the expected user was created
        users = api_users_pg.get(username='it_user1')
        assert users.count == 1
        user = users.results[0]

        # Verify the expected team was created
        teams = user.get_related('teams', name='LDAP IT')
        assert teams.count == 1

        # Verify expected organization was created
        orgs = user.get_related('organizations', name='LDAP Organization')
        assert orgs.count == 1

    def test_org_admin_ldap_user(self, install_legacy_license, cleanup_ldap_info, api_users_pg, user_password):
        """Verified that an LDAP organization admin relationship is created at login."""
        with self.current_user(username='eng_admin1', password=user_password):
            user = api_users_pg.get(username='eng_admin1').results[0]
            orgs = user.get_related('admin_of_organizations', name="LDAP Organization")
            assert orgs.count == 1

    def test_license_enables_ldap_authentication(self, api_users_pg, user_password, ldap_enabled_license):
        """Verified Tower supports LDAP authentication with a supported license."""
        with self.current_user(username='eng_user1', password=user_password):
            api_users_pg.get(username='eng_user1')

    def test_license_disables_ldap_authentication(self, api_users_pg, user_password, ldap_disabled_license):
        """Verified Tower disables LDAP authentication with an unsupported license."""
        with pytest.raises(towerkit.exceptions.Unauthorized):
            with self.current_user(username='sales_user1', password=user_password):
                api_users_pg.get(username='sales_user1')
