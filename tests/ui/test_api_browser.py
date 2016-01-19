import pytest


@pytest.mark.skipif(True, reason='Needs to be updated with 3.0 page models')
class Test_Api_Browser(object):

    def test_home_pg(self, mozwebqa):
        home_pg = Api_Browser_Home(mozwebqa)
        home_pg.open()
        assert home_pg.is_the_current_page, "Unable to determine if API browser loaded successfully"

        v1_pg = home_pg.click_v1_link()
        assert v1_pg.is_the_current_page, "Unable to determine if page loaded successfully"

    def TODO_test_login(self, mozwebqa):
        '''handling http auth alert dialog doesn't yet work'''
        home_pg = Api_Browser_Home(mozwebqa)
        home_pg.open()
        v1_pg = home_pg.click_by_href('/api/v1/')
        config_pg = v1_pg.click_by_href('/api/v1/config/')
        config_pg.login()
        assert home_pg.is_logged_in, 'Unable to determine if logged in'
