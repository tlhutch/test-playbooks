import pytest
from tests.ui import Base_UI_Test


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Main_Menu(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

    def test_menu_items(self, ui_dashboard_pg):
        '''
        Verify the main_menu contents for a logged in user
        '''

        # assert the active tab
        assert ui_dashboard_pg.is_the_active_tab

        actual_items = ui_dashboard_pg.header.main_menu.keys()
        expected_items = [u'Organizations', u'Users', u'Teams', u'Credentials',
                          u'Projects', u'Inventories', u'Job Templates', u'Jobs']

        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Account_Menu(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

    def test_superuser_menu_items(self, ui_dashboard_pg):
        '''
        Verify the main_menu contents for a superuser.
        '''

        assert ui_dashboard_pg.is_the_active_tab

        ui_dashboard_pg.header.account_menu.show()
        actual_items = ui_dashboard_pg.header.account_menu.keys()
        expected_items = [u'About Tower', u'Account Settings', u'Contact Support',
                          u'Inventory Script', u'Management Jobs', u'Monitor Tower',
                          u'Portal Mode', u'View License', u'Logout']

        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_non_superuser_menu_items(self, ui_dashboard_pg, non_superuser, user_password):
        '''
        Verify the main_menu contents for a non-superuser
        '''

        with self.current_user(non_superuser.username, user_password):
            assert ui_dashboard_pg.header.current_user == non_superuser.username
            assert ui_dashboard_pg.is_the_active_tab

            ui_dashboard_pg.header.account_menu.show()
            actual_items = ui_dashboard_pg.header.account_menu.keys()
            expected_items = [u'About Tower', u'Account Settings', u'Contact Support',
                              u'Portal Mode', u'View License', u'Logout']

            assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_non_superuser_menu_items_after_exiting_portal(self, ui_dashboard_pg, non_superuser, user_password):
        '''
        Verify the account menu items are correct upon returning from portal mode.

        Trello: https://trello.com/c/AuT9wUmw
        '''

        with self.current_user(non_superuser.username, user_password):

            # assert dashboard page
            assert ui_dashboard_pg.is_the_active_tab
            # assert expected user
            assert ui_dashboard_pg.header.current_user == non_superuser.username

            # enter portal mode
            ui_portal_pg = ui_dashboard_pg.header.account_menu.click("Portal Mode")

            # assert portal mode page
            assert ui_portal_pg.is_the_active_tab

            # assert expected user
            assert ui_portal_pg.header.current_user == non_superuser.username

            # exit portal mode
            ui_dashboard_pg = ui_portal_pg.header.account_menu.click("Exit Portal")

            # show the account menu
            ui_dashboard_pg.header.account_menu.show()

            # assert expected menu items
            actual_items = ui_dashboard_pg.header.account_menu.keys()
            expected_items = [u'About Tower', u'Account Settings', u'Contact Support',
                              u'Portal Mode', u'View License', u'Logout']
            assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Portal_Menu(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

    def test_menu_items(self, ui_portal_pg):
        '''
        Verify the account menu contents when in Portal mode.
        '''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # show the account menu
        ui_portal_pg.header.account_menu.show()

        # assert expected menu items
        actual_items = ui_portal_pg.header.account_menu.keys()
        expected_items = [u'About Tower', u'Exit Portal', u'Logout']
        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Mobile_Menu(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('window_mobile', 'install_license_unlimited')

    def test_visibility(self, ui_dashboard_pg):
        '''
        Verify that the mobile_menu is displayed, while the main_menu and
        account_menu are hidden.
        '''

        # assert dashboard is the active tab
        assert ui_dashboard_pg.is_the_active_tab

        # assert the main_menu is hidden
        assert not ui_dashboard_pg.header.main_menu.is_displayed()

        # assert the account_menu is hidden
        assert not ui_dashboard_pg.header.account_menu.is_displayed()

        # assert the mobile_menu is displayed
        assert ui_dashboard_pg.header.mobile_menu.is_displayed()

    def test_superuser_menu_items(self, ui_dashboard_pg):
        '''
        Verify the expected mobile_menu items when logged in as a superuser.
        '''

        # assert dashboard is the active tab
        assert ui_dashboard_pg.is_the_active_tab

        # assert the mobile_menu is displayed
        assert ui_dashboard_pg.header.mobile_menu.is_displayed()

        ui_dashboard_pg.header.mobile_menu.show()
        actual_items = ui_dashboard_pg.header.mobile_menu.keys()
        expected_items = [u'Home', u'Organizations', u'Users', u'Teams', u'Credentials',
                          u'Projects', u'Inventories', u'Job Templates', u'Jobs',
                          u'About Tower', u'Account Settings', u'Contact Support',
                          u'Inventory Script', u'Management Jobs', u'Monitor Tower',
                          u'Portal Mode', u'View License', u'Logout']

        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_non_superuser_menu_items(self, ui_dashboard_pg, non_superuser, user_password):
        '''
        Verify the expected mobile_menu items when logged in as a non-superuser.
        '''

        with self.current_user(non_superuser.username, user_password):
            assert ui_dashboard_pg.header.current_user == non_superuser.username

            # assert dashboard is the active tab
            assert ui_dashboard_pg.is_the_active_tab

            # assert the mobile_menu is displayed
            assert ui_dashboard_pg.header.mobile_menu.is_displayed()

            # assert the mobile_menu contents
            ui_dashboard_pg.header.mobile_menu.show()
            actual_items = ui_dashboard_pg.header.mobile_menu.keys()
            expected_items = [u'Home', u'Organizations', u'Users', u'Teams', u'Credentials',
                              u'Projects', u'Inventories', u'Job Templates', u'Jobs',
                              u'About Tower', u'Account Settings', u'Contact Support',
                              u'Portal Mode', u'View License', u'Logout']

            assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)

    def test_portal_menu_items(self, ui_portal_pg):
        '''
        Verify the mobile menu contents when in Portal mode.
        '''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        ui_portal_pg.header.mobile_menu.show()
        actual_items = ui_portal_pg.header.mobile_menu.keys()
        expected_items = [u'Exit Portal', u'Logout']

        assert actual_items == expected_items, "Missing expected menu items (%s != %s)" % (actual_items, expected_items)
