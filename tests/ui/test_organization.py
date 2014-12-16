import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def accordions(request):
    return ('Properties', 'Users', 'Administrators')


@pytest.fixture(scope="function", params=["Name", "Description"])
def search_filter(request):
    return request.param


@pytest.fixture(scope="function")
def table_sort(request, admin_user, org_admin):
    return [('name', 'ascending'),
            ('name', 'descending'),
            ('description', 'ascending'),
            ('description', 'descending')]


@pytest.mark.ui
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

    def test_sort(self, many_organizations, table_sort, ui_organizations_pg):
        '''Verify organiation table sorting'''
        assert ui_organizations_pg.is_the_active_tab

        # Verify default table sort column and order
        self.assert_table_sort(ui_organizations_pg.table, *table_sort[0])

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_organizations_pg.table.sort_by(sorted_by, sort_order)

            # Verify table sort column and order
            self.assert_table_sort(ui_organizations_pg.table, sorted_by, sort_order)

    def test_no_pagination(self, authtoken, api_organizations_pg, ui_organizations_pg):
        '''Verify organiation table pagination is not present'''

        if api_organizations_pg.get().count > ui_organizations_pg.pagination.page_size:
            pytest.skip("Unable to test as too many organizations exist")

        # Pagination present
        assert ui_organizations_pg.pagination.is_displayed()
        # Pagination labels present
        assert ui_organizations_pg.pagination.labels.is_displayed()
        # Pagination links shouldn't display
        assert not ui_organizations_pg.pagination.links.is_displayed(), \
            "Pagination present, but fewer than %d organizations are visible" % \
            ui_organizations_pg.pagination.page_size

    def test_pagination(self, many_organizations, api_organizations_pg, ui_organizations_pg):
        '''Verify organiation table pagination'''

        assert ui_organizations_pg.pagination.is_displayed(), "Unable to find pagination"

        # TODO: Verify expected number of items in pagination
        total_count = api_organizations_pg.get().count
        total_pages = int(ceil(total_count / float(ui_organizations_pg.pagination.page_size)))

        # Click next_pg until reaching the end
        curr_pg = ui_organizations_pg
        pages_seen = 1
        while curr_pg.pagination.next_page.is_displayed():
            # assert pagination links
            self.assert_page_links(curr_pg, pages_seen, total_pages)
            # click next_page
            curr_pg = curr_pg.pagination.next_page.click()
            pages_seen += 1

        # assert last page
        self.assert_page_links(curr_pg, pages_seen, total_pages)

        assert pages_seen == total_pages, \
            "Unexpected number of pages seen (%s != %s)" % \
            (pages_seen, total_pages)

        # Click prev_pg until reaching the beginning
        while curr_pg.pagination.prev_page.is_displayed():
            # assert pagination links
            self.assert_page_links(curr_pg, pages_seen, total_pages)
            # click prev_page
            curr_pg = curr_pg.pagination.prev_page.click()
            pages_seen -= 1

        # assert first page
        self.assert_page_links(curr_pg, pages_seen, total_pages)

        assert pages_seen == 1, \
            "Unexpected number of pages seen (%s != %s)" % \
            (pages_seen, 1)

        # TODO: click page#2
        # next_pg = curr_pg.pagination.get(2).click()

    def test_filter(self, organization, search_filter, ui_organizations_pg):
        '''Verify organiation table filtering using a name'''
        assert ui_organizations_pg.is_the_active_tab
        search_value = getattr(organization, search_filter.replace(' ', '_').lower())

        # search by name
        ui_organizations_pg.search.search_type.select(search_filter)
        ui_organizations_pg.search.search_value = search_value
        ui_organizations_pg = ui_organizations_pg.search.search_btn.click()

        # verify expected number of items found
        assert ui_organizations_pg.pagination.total_items == 1, \
            "Unexpected number of results (%d != %d)" % \
            (ui_organizations_pg.pagination.total_items, 1)
        # verify expected matching row
        assert ui_organizations_pg.table.find_row(search_filter, search_value)

        # reset search filter
        ui_organizations_pg = ui_organizations_pg.search.reset_btn.click()
        assert ui_organizations_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_organizations_pg.search.search_value

    def test_filter_notfound(self, organization, ui_organizations_pg):
        '''Verify organiation table filtering using a bogus value'''
        assert ui_organizations_pg.is_the_active_tab

        # search for an org that doesn't exist
        ui_organizations_pg.search.search_value = common.utils.random_unicode()
        ui_organizations_pg = ui_organizations_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_organizations_pg.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_organizations_pg.pagination.total_items, 0)
        assert ui_organizations_pg.table.find_row("name", "No records matched your search.")

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

    def test_table_edit_icon(self, ui_organizations_pg, organization):
        '''Verify the edit-action spawns an organization edit page when clicked'''

        ui_organizations_pg.search.search_value = organization.name
        ui_organizations_pg.search.search_btn.click()
        edit_pg = ui_organizations_pg.table.find_row('name', organization.name).actions.click("edit-action")
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

    def test_table_delete_icon(self, ui_organizations_pg, organization):
        '''Verify the delete-action spawns an organization delete region when clicked'''

        ui_organizations_pg.search.search_value = organization.name
        ui_organizations_pg.search.search_btn.click()
        delete_pg = ui_organizations_pg.table.find_row('name', organization.name).actions.click("edit-action")
        assert delete_pg.is_the_active_tab
        assert delete_pg.is_the_active_breadcrumb

    def test_org_activity_stream(self, organization, ui_organizations_pg):
        '''Verify that the organization activity stream can be open and closed'''

        edit_pg = ui_organizations_pg.open(organization.id)
        assert edit_pg.accordion.get('Properties')[0].is_expanded(), "The properties accordion was not expanded as expected"
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Open activity_stream
        org_activity_pg = edit_region.activity_stream_btn.click()
        assert org_activity_pg.is_the_active_tab
        assert org_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        org_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_organizations_pg = org_activity_pg.close_btn.click()
        assert ui_organizations_pg.is_the_active_tab

    def test_accordions(self, ui_organizations_pg, organization, accordions):
        '''Verify the organiation accordions behave properly'''
        # Open edit page
        edit_pg = ui_organizations_pg.open(organization.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Assert default accordions configuration
        assert edit_pg.accordion.get('Properties')[0].is_expanded(), "The properties accordion was not expanded as expected"
        for title in accordions[1:]:
            assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title

        # Expand and collapse each accordion
        for title_expand in accordions[1:]:
            edit_pg.accordion.get(title_expand)[0].expand()
            # Assert correct expand/collapse state for all accordions
            for title in accordions:
                if title == title_expand:
                    assert edit_pg.accordion.get(title)[0].is_expanded(), "The %s accordion was not expand as expected" % title
                else:
                    assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title

        # Re-open edit page and verify last accordion is expanded
        edit_pg = ui_organizations_pg.open(organization.id)
        for title in accordions[:-1]:
            assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title
        assert edit_pg.accordion.get(accordions[-1])[0].is_expanded(), "The %s accordion was not expanded as expected" % accordions[-1]

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
        assert edit_region.name == organization.name, \
            "The reset button did not restore the 'name' (%s != %s)" % \
            (edit_region.name, organization.name)
        assert edit_region.description == organization.description, \
            "The reset button did not restore the 'description' (%s != %s)" % \
            (edit_region.description, organization.description)

    def test_associate_user(self, organization, anonymous_user, ui_organizations_pg):
        '''Verify basic operation of associating users'''
        edit_pg = ui_organizations_pg.open(organization.id)
        region = edit_pg.accordion.click("Users")

        # assert disassociation
        assert region.table.find_row('username', anonymous_user.username) is None, \
            "User (%s) unexpectedly associated with organization (%s)" % (anonymous_user.username, organization.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # filter for item
        add_pg.search.search_value = anonymous_user.username
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(username=anonymous_user.username), 'username')
        edit_pg = add_pg.select_btn.click()
        assert edit_pg.accordion.get("Users")[0].is_expanded(), "The Users accordion was not expanded as expected"
        region = edit_pg.accordion.click("Users")

        # assert association
        assert region.table.find_row('username', anonymous_user.username) is not None, \
            "User (%s) was not properly associated with organization (%s)" % (anonymous_user.username, organization.name)

    def test_associate_admin(self, organization, anonymous_user, org_user, ui_organizations_pg):
        '''Verify basic operation of associating administrators'''
        edit_pg = ui_organizations_pg.open(organization.id)
        region = edit_pg.accordion.click("Administrators")

        # assert disassociation
        assert region.table.find_row('username', org_user.username) is None, \
            "User (%s) unexpectedly associated with organization (%s)" % (org_user.username, organization.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # assert anonymous_user is *not* present
        assert add_pg.table.find_row('username', anonymous_user.username) is None, \
            "Anonymous user (%s) unexpectedly available for association with organization (%s)" % (anonymous_user.username, organization.name)

        # filter for and select desired item
        add_pg.search.search_value = org_user.username
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(username=org_user.username), 'username')
        edit_pg = add_pg.select_btn.click()

        # assert expected accordion
        assert edit_pg.accordion.get("Administrators")[0].is_expanded(), "The Administrators accordion was not expanded as expected"
        region = edit_pg.accordion.click("Administrators")

        # assert successful association
        assert region.table.find_row('username', org_user.username) is not None, \
            "Administrator (%s) was not properly associated with organization (%s)" % (org_user.username, organization.name)


# @pytest.mark.nondestructive
# class Test_Organization_LowRes(Base_UI_Test):
