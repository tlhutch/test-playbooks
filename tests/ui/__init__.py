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
