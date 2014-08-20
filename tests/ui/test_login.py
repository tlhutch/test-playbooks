#!/usr/bin/env python

import pytest
from common.ui.pages import LoginPage
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
class TestLogin(Base_UI_Test):
    @pytest.mark.nondestructive
    def test_login(self, home_page_logged_in):
        '''If the fixture setup works correctly, login was successful'''
        assert True

    def test_logout(self, home_page_logged_in):
        assert home_page_logged_in.is_logged_in, "Unable to determine if logged in"
        home_page_logged_in.header.account_menu.show()
        home_page_logged_in.header.account_menu.click_logout()
        assert not home_page_logged_in.is_logged_in, "Unable to determine if logged out"
