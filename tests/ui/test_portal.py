import pytest
import common.utils
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Portal(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_account_menu(self, ui_portal_pg):
        '''Verify a navigating to /#/portal, and logging in, correctly returns the portal page'''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # exit portal mode
        dashboard_pg = ui_portal_pg.account_menu.click('Exit Portal')

        # assert the dashboard is the active tab
        assert dashboard_pg.is_the_active_tab

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_redirect_after_timeout(self, ui_portal_pg):
        '''Verify a that login after an auth-token timeout, while viewing /#/portal page, returns the user to the portal page'''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # simulate a auth-cookie timeout
        ui_portal_pg.selenium.delete_cookie('token')
        # simulate a auth-cookie timeout
        ui_portal_pg.selenium.refresh()

        # FIXME - login

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_job_template_region(self):
        '''Verify a that ob_templates region includes expected actions and links'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_jobs_region(self):
        '''Verify a that jobs region includes expected actions and links'''

    @pytest.mark.skipif(True, reason="FIXME - UI portal tests coming soon!")
    def test_jobs_only_includes_playbook_runs(self):
        '''Verify a that jobs region only shows jobs of type=playbook_run'''
