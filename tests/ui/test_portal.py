import pytest
import urllib
import common.utils
from tests.ui import Base_UI_Test
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Portal(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_account_menu(self, ui_portal_pg):
        '''Verify a navigating to /#/portal, and logging in, correctly redirects the to the portal page'''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # exit portal mode
        dashboard_pg = ui_portal_pg.account_menu.click('Exit Portal')

        # assert the dashboard is the active tab
        assert dashboard_pg.is_the_active_tab

    # @pytest.mark.fixture_args(login=False)
    def test_redirect_after_first_login(self, mozwebqa):
        '''
        Verify a that accessing Tower for the first time, using the
        /#/portal URL, redirects to the portal page after successful login.
        '''

        # TODO: it'd be nice to have a fixture that returns the page object, but does *not* login
        from common.ui.pages import Portal_Page
        ui_portal_pg = Portal_Page(mozwebqa)
        ui_portal_pg.open('/#/portal')

        # assert login prompt visible
        assert ui_portal_pg.has_login_dialog, "Unable to find the login dialog as expected"

        # login
        ui_portal_pg.login_dialog.login()

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

    def test_redirect_after_login_timeout(self, ui_portal_pg):
        '''Verify a that login after an auth-token timeout, while viewing /#/portal page, returns the user to the portal page'''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # simulate a auth-cookie timeout
        # get token_expires cookie
        if True:
            ui_portal_pg.selenium.delete_cookie('token')
        else:
            # set token_expires cookie
            token_expires = ui_portal_pg.selenium.get_cookie('token_expires')
            token_expires['value'] = urllib.unquote(token_expires['value'])

            # delete token_expires cookie
            ui_portal_pg.selenium.delete_cookie('token_expires')

            # add modified token_expires
            token_expires['value'] = parse(token_expires['value'], fuzzy=True) - relativedelta(hours=6)
            token_expires['value'] = token_expires['value'].strftime('"%Y-%m-%dT%H:%M:%S.%fZ"')
            ui_portal_pg.selenium.add_cookie(token_expires)

        # refresh the page
        ui_portal_pg.refresh()

        # assert login prompt visible
        assert ui_portal_pg.has_login_dialog, "Unable to find the login dialog as expected"

        # login
        ui_portal_pg.login_dialog.login()

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_job_template_region(self):
        '''Verify a that jobs region includes expected actions and links'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_jobs_region(self):
        '''Verify a that jobs region includes expected actions and links'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_jobs_only_includes_playbook_runs(self):
        '''Verify a that jobs region only shows jobs of type=playbook_run'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_job_template_launch(self):
        '''Verify expected behavior when launching a job_template within portal mode.'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_job_details(self):
        '''Verify expected behavior when launching a job_template within portal mode.'''
