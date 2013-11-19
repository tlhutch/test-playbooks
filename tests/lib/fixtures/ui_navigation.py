import pytest
from common.ui.pages import *
from unittestzero import Assert

@pytest.fixture
def home_page_logged_in(mozwebqa):
    '''Logs in to the application with default credentials and returns the
    home page'''
    login_pg = LoginPage(mozwebqa)
    login_pg.go_to_login_page()
    home_pg = login_pg.login()
    assert home_pg.is_logged_in, 'Unable to determine if logged in'
    return home_pg

def _submenu(home_pg, main_menu, submenu):
    return home_pg.header.site_navigation_menu(
            main_menu).sub_navigation_menu(submenu).click()

@pytest.fixture
def ui_organizations_pg(home_page_logged_in):
    '''Navigate to the Organizations tab and return it'''
    return home_pg.header.site_navigation_menu('Organizations').click()

@pytest.fixture
def ui_users_pg(home_page_logged_in):
    '''Navigate to the Users tab and return it'''
    return home_pg.header.site_navigation_menu('Users').click()

@pytest.fixture
def ui_teams_pg(home_page_logged_in):
    '''Navigate to the Teams tab and return it'''
    return home_pg.header.site_navigation_menu('Teams').click()

@pytest.fixture
def ui_credentials_pg(home_page_logged_in):
    '''Navigate to the Credentials tab and return it'''
    return home_pg.header.site_navigation_menu('Credentials').click()

@pytest.fixture
def ui_projects_pg(home_page_logged_in):
    '''Navigate to the Projects tab and return it'''
    return home_pg.header.site_navigation_menu('Projects').click()

@pytest.fixture
def ui_inventories_pg(home_page_logged_in):
    '''Navigate to the Inventories tab and return it'''
    return home_pg.header.site_navigation_menu('Inventories').click()

@pytest.fixture
def ui_job_Templates_pg(home_page_logged_in):
    '''Navigate to the Job_Templates tab and return it'''
    return home_pg.header.site_navigation_menu('Job Templates').click()

@pytest.fixture
def ui_jobs_pg(home_page_logged_in):
    '''Navigate to the Jobs tab and return it'''
    return home_pg.header.site_navigation_menu('Jobs').click()
