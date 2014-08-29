import pytest
import common.utils
from tests.ui import Base_UI_Test


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Organization(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_organizations_pg):
        '''Verify the basics of the organizations page'''
        assert ui_organizations_pg.is_the_active_tab

        # FIXME - assert 'organizations' table is visible (id=organizations_table)
        # FIXME - assert 'organizations' search box is visible (id=search-widget-container)

    def test_activity_stream(self, ui_organizations_pg):
        '''Verify that the organization activity stream can be open and closed'''
        # Open activity_stream
        orgs_activity_pg = ui_organizations_pg.activity_stream_btn.click()
        assert orgs_activity_pg.is_the_active_tab
        assert orgs_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        orgs_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_organizations_pg = orgs_activity_pg.close_btn.click()
        assert ui_organizations_pg.is_the_active_tab

    def test_add(self, ui_organizations_pg):
        '''Verify basic organiation form fields'''
        assert ui_organizations_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_organizations_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        add_pg.name = "Random Organization - %s" % common.utils.random_unicode()
        add_pg.description = "Random description - %s" % common.utils.random_unicode()

        # Click Reset
        add_pg.reset_btn.click()
        assert add_pg.name == "", "Reset button did not reset the field: name"
        assert add_pg.description == "", "Reset button did not reset the field: description"

    def test_accordions(self, ui_organizations_pg, organization):
        '''Verify the organiation accordions behave properly'''
        # Open edit page
        edit_pg = ui_organizations_pg.open(organization.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Assert default collapsed accordions
        assert edit_pg.accordion.get('Properties')[0].is_expanded(), "The properties accordion was not expanded as expected"
        assert edit_pg.accordion.get('Users')[0].is_collapsed(), "The users accordion was not collapsed as expected"
        assert edit_pg.accordion.get('Administrators')[0].is_collapsed(), "The administrators accordion was not collapsed as expected"

        # Expand the Users accordion
        edit_pg.accordion.get('Users')[0].expand()
        assert edit_pg.accordion.get('Properties')[0].is_collapsed(), "The properties accordion was not collapse as expected"
        assert edit_pg.accordion.get('Users')[0].is_expanded(), "The users accordion was not expand as expected"
        assert edit_pg.accordion.get('Administrators')[0].is_collapsed(), "The administrators accordion was not collapse as expected"

        # Re-open edit page and verify accordion memory
        edit_pg = ui_organizations_pg.open(organization.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.accordion.get('Properties')[0].is_collapsed(), "The properties accordion was not collapse as expected"
        assert edit_pg.accordion.get('Users')[0].is_expanded(), "The users accordion was not expand as expected"
        assert edit_pg.accordion.get('Administrators')[0].is_collapsed(), "The administrators accordion was not collapse as expected"

    def test_edit_properties(self, ui_organizations_pg, organization):
        '''Verify basic organiation form fields when editing an organization'''
        edit_pg = ui_organizations_pg.open(organization.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access the edit region
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Modify organization form fields
        edit_region.name = common.utils.random_unicode()
        edit_region.description = common.utils.random_unicode()

        # Verify breadcrumb title updated
        assert edit_pg.is_the_active_breadcrumb

        # Reset Edit form
        edit_region.reset_btn.click()
        assert edit_pg.is_the_active_breadcrumb
        assert edit_region.name == organization.name, "The reset button did not restore the 'name' (%s != %s)" % (edit_region.name, organization.name)
        assert edit_region.description == organization.description, "The reset button did not restore the 'description' (%s != %s)" % (edit_region.description, organization.description)

    def FIXME_test_edit_users(self, ui_organizations_pg, organization):
        '''Verify basic operation of organizations users accordion'''
        edit_pg = ui_organizations_pg.open(organization.id)
        # Access the users region
        users_region = edit_pg.accordion.get('Users')[1]

    def FIXME_test_edit_admins(self, ui_organizations_pg, organization):
        '''Verify basic operation of organizations admins accordion'''

        edit_pg = ui_organizations_pg.open(organization.id)
        # Access the users region
        admins_region = edit_pg.accordion.get('Administrators')[1]
