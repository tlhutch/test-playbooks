#!/usr/bin/env python

import pytest
from common.ui.pages import Api_Browser_Home
from tests.ui import Base_UI_Test

@pytest.mark.usefixtures("maximized")
class Test_Api_Browser(Base_UI_Test):

    @pytest.mark.nondestructive
    def test_home_pg(self, mozwebqa):
        home_pg = Api_Browser_Home(mozwebqa)
        home_pg.go_to_login_page()
        assert home_pg.is_the_current_page, "Unable to determine if API browser loaded successfully"

        v1_pg = home_pg.click_v1_link()
        assert v1_pg.is_the_current_page, "Unable to determine if page loaded successfully"

#    @pytest.mark.nondestructive
#    def test_login(self, mozwebqa):
#        '''handling http auth alert dialog doesn't yet work'''
#        home_pg = Api_Browser_Home(mozwebqa)
#        home_pg.go_to_login_page()
#        v1_pg = home_pg.click_by_href('/api/v1/')
#        config_pg = v1_pg.click_by_href('/api/v1/config/')
#        config_pg.login()
#        assert home_pg.is_logged_in, 'Unable to determine if logged in'

