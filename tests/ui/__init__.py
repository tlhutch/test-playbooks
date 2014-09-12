import pytest
import contextlib

@pytest.mark.selenium
class Base_UI_Test(object):
    '''
    Base class
    '''
    @classmethod
    def setup_class(self):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        plugin = pytest.config.pluginmanager.getplugin("mozwebqa")
        assert plugin, 'Unable to find mozwebqa plugin'
        self.testsetup = plugin.TestSetup

        # plugin = pytest.config.pluginmanager.getplugin("plugins.pytest_restqa.pytest_restqa")
        # assert plugin, 'Unable to find pytest_restqa plugin'
        # self.testsetup = plugin.TestSetup

    @classmethod
    def teardown_class(self):
        '''
        Perform any required test teardown
        '''

    @property
    def credentials(self):
        '''convenient access to credentials'''
        return self.testsetup.credentials

    @property
    def api(self):
        '''convenient access to api'''
        return self.testsetup.api

    def has_credentials(self, ctype, sub_ctype=None, fields=[]):
        '''
        assert whether requested credentials are present
        '''

        # Make sure credentials.yaml has ctype we need
        assert ctype in self.testsetup.credentials, \
            "No '%s' credentials defined in credentals.yaml" % ctype
        creds = self.testsetup.credentials[ctype]

        # Ensure requested sub-type is present
        if sub_ctype:
            assert sub_ctype in creds, \
                "No '%s' '%s' credentials defined in credentals.yaml" % \
                (ctype, sub_ctype)
            creds = creds[sub_ctype]

        # Ensure requested fields are present
        if fields:
            assert all([field in creds for field in fields]), \
                "Not all requested credential fields for section '%s' defined credentials.yaml" % \
                ctype

        return True

    @contextlib.contextmanager
    def current_user(self, username, password):
        from common.ui.pages.login import Login_Page
        # raise NotImplementedError("UI support for the context manager is not yet implemented")

        previous_cookies = list()
        try:
            '''login as the provided user'''
            # Add credentials so login_pg knows what to do
            self.credentials['users'][username] = dict(username=username, password=password)

            # save cookies
            previous_cookies = self.testsetup.selenium.get_cookies()

            # set new cookies
            # new_auth = self.api.login(username, password)
            login_pg = Login_Page(self.testsetup)
            if login_pg.is_logged_in:
                login_pg.logout()
            # login_pg.go_to_login_page()
            login_pg.login(username)

            # refresh the current page
            # self.testsetup.selenium.refresh()
            yield

        finally:
            '''restore authentication'''
            # restore previous cookies
            for cookie in previous_cookies:
                self.testsetup.selenium.add_cookie(cookie)

            # refresh the current page
            self.testsetup.selenium.refresh()
            login_pg.wait_for_spinny()

            # $cookieStore.put('token', token);
            # $cookieStore.put('token_expires', expires);
            # $cookieStore.put('userLoggedIn', true);
            # $cookieStore.put('sessionExpired', false);

    @staticmethod
    def assert_page_links(page, current_page, total_pages):
        '''
        Convenience method to assert expected pagination links
        '''
        # Assert expected pagination links
        assert page.pagination.current_page == current_page, \
            "Unexpected current page number (%d != %d)" % \
            (page.pagination.current_page, current_page)
        # assert first_page link?
        assert not page.pagination.first_page.is_displayed()
        # assert prev_page link?
        if page.pagination.current_page == 1:
            assert not page.pagination.prev_page.is_displayed()
        else:
            assert page.pagination.prev_page.is_displayed()
        # assert next_page link?
        if page.pagination.current_page == total_pages:
            assert not page.pagination.next_page.is_displayed()
        else:
            assert page.pagination.next_page.is_displayed()
        # assert last_page link?
        assert not page.pagination.last_page.is_displayed()
        # assert page count
        assert page.pagination.count() == total_pages, \
            "Unexpected number of pagination links (%d != %d)" % \
            (page.pagination.count(), total_pages)

    @staticmethod
    def assert_table_sort(table, sorted_by, sort_order):
        '''
        Convenience method to assert the desired table sort and order
        '''
        # Verify new table sort column
        assert table.sorted_by == sorted_by, \
            "Unexpected default table sort column (%s != %s)" % \
            (table.sorted_by, sorted_by)

        # Verify new table sort order
        assert table.sort_order == sort_order, \
            "Unexpected default table sort order (%s != %s)" % \
            (table.sort_order, sort_order)
