#!/usr/bin/env python

import pytest
from common.ui.pages import LoginPage
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
class TestLogin(Base_UI_Test):
    @pytest.mark.nondestructive
    def test_login(self, mozwebqa):
        login_pg = LoginPage(mozwebqa)
        login_pg.go_to_login_page()
        home_pg = login_pg.login()
        assert home_pg.is_logged_in, "Unable to determine if logged in"
