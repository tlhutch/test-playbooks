import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def accordions(request):
    return ('Properties', 'Credentials', 'Permissions', 'Projects', 'Users')


@pytest.fixture(scope="function")
def table_sort(request):
    return [('name', 'ascending'),
            ('name', 'descending'),
            ('description', 'ascending'),
            ('description', 'descending'),
            ('organization', 'ascending'),
            ('organization', 'descending')]


@pytest.fixture(scope="function")
def FIXME_many_teams(request, authtoken, organization):

    obj_list = list()
    for i in range(55):
        payload = dict(name="%s many teams" % common.utils.random_unicode(),
                       description="Some Random Team (%s)" % common.utils.random_unicode(),
                       organization=organization.id,)
        obj = organization.get_related('teams').post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Teams(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_teams_pg):
        '''Verify the basics of the teams page'''
        assert ui_teams_pg.is_the_active_tab

        # FIXME - assert 'teams' table is visible (id=teams_table)
        # FIXME - assert 'teams' search box is visible (id=search-widget-container)

    def test_activity_stream(self, ui_teams_pg):
        '''Verify that the team activity stream can be open and closed'''
        # Open activity_stream
        orgs_activity_pg = ui_teams_pg.activity_stream_btn.click()
        assert orgs_activity_pg.is_the_active_tab
        assert orgs_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        orgs_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_teams_pg = orgs_activity_pg.close_btn.click()
        assert ui_teams_pg.is_the_active_tab

    def test_sort(self, many_teams, table_sort, ui_teams_pg):
        '''Verify table sorting'''
        assert ui_teams_pg.is_the_active_tab

        # Verify default table sort column
        assert ui_teams_pg.table.sorted_by == 'name', \
            "Unexpected default table sort column (%s != %s)" % \
            (ui_teams_pg.table.sorted_by, 'name')

        # Verify default table sort order
        assert ui_teams_pg.table.sort_order == 'ascending', \
            "Unexpected default table sort order (%s != %s)" % \
            (ui_teams_pg.table.sort_order, 'ascending')

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_teams_pg.table.sort_by(sorted_by, sort_order)

            # Verify new table sort column
            assert ui_teams_pg.table.sorted_by == sorted_by, \
                "Unexpected default table sort column (%s != %s)" % \
                (ui_teams_pg.table.sorted_by, sorted_by)

            # Verify new table sort order
            assert ui_teams_pg.table.sort_order == sort_order, \
                "Unexpected default table sort order (%s != %s)" % \
                (ui_teams_pg.table.sort_order, sort_order)

    def test_no_pagination(self, authtoken, api_teams_pg, ui_teams_pg):
        '''Verify table pagination is not present'''

        if api_teams_pg.get().count > ui_teams_pg.pagination.page_size:
            pytest.skip("Unable to test as too many teams exist")

        # Pagination present
        assert ui_teams_pg.pagination.is_displayed()
        # Pagination labels present
        assert ui_teams_pg.pagination.labels.is_displayed()
        # Pagination links shouldn't display
        assert not ui_teams_pg.pagination.links.is_displayed(), \
            "Pagination present, but fewer than %d teams are visible" % \
            ui_teams_pg.pagination.page_size

    def test_pagination(self, many_teams, ui_teams_pg, api_teams_pg):
        '''Verify table pagination'''

        assert ui_teams_pg.pagination.is_displayed(), "Unable to find pagination"

        # TODO: Verify expected number of items in pagination
        total_count = api_teams_pg.get().count
        total_pages = int(ceil(total_count / float(ui_teams_pg.pagination.page_size)))

        # Click next_pg until reaching the end
        curr_pg = ui_teams_pg
        pages_seen = 1
        while curr_pg.pagination.next_page.is_displayed():
            # assert expected pagination links
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
            # assert expected pagination links
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

    def test_filter_name(self, team, ui_teams_pg):
        '''Verify table filtering using a name'''
        assert ui_teams_pg.is_the_active_tab

        # search by name
        ui_teams_pg.search.search_type.select("Name")
        ui_teams_pg.search.search_value = team.name
        ui_teams_pg = ui_teams_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_teams_pg.pagination.total_items == 1
        num_rows = len(list(ui_teams_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_teams_pg.table.find_row("name", team.name)

        # reset search filter
        ui_teams_pg = ui_teams_pg.search.reset_btn.click()
        assert ui_teams_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_teams_pg.search.search_value

    def test_filter_description(self, team, ui_teams_pg):
        '''Verify table filtering using a description'''
        assert ui_teams_pg.is_the_active_tab

        # search by description
        ui_teams_pg.search.search_type.select("Description")
        ui_teams_pg.search.search_value = team.description
        ui_teams_pg = ui_teams_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_teams_pg.pagination.total_items == 1
        num_rows = len(list(ui_teams_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_teams_pg.table.find_row("description", team.description)

        # reset search filter
        ui_teams_pg = ui_teams_pg.search.reset_btn.click()
        assert ui_teams_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_teams_pg.search.search_value

    def test_filter_notfound(self, team, ui_teams_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_teams_pg.is_the_active_tab

        # Search for an org that doesn't exist
        ui_teams_pg.search.search_type.select("Name")
        ui_teams_pg.search.search_value = common.utils.random_unicode()
        ui_teams_pg = ui_teams_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_teams_pg.pagination.total_items == 1
        num_rows = len(list(ui_teams_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_teams_pg.table.find_row("name", "No records matched your search.")

    def test_add(self, organization, ui_teams_pg):
        '''Verify basic form fields'''
        assert ui_teams_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_teams_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        add_pg.name = "Random Team - %s" % common.utils.random_unicode()
        add_pg.description = "Random description - %s" % common.utils.random_unicode()
        add_pg.organization_name = organization.name

        # Click Reset
        add_pg.reset_btn.click()
        assert add_pg.name == "", "Reset button did not reset the field: name"
        assert add_pg.description == "", "Reset button did not reset the field: description"
        assert add_pg.organization_name == "", "Reset button did not reset the field: organization_name"

    def test_team_activity_stream(self, team, ui_teams_pg):
        '''Verify that the team activity stream can be open and closed'''

        # Open edit page
        edit_pg = ui_teams_pg.open(team.id)
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
        ui_teams_pg = org_activity_pg.close_btn.click()
        assert ui_teams_pg.is_the_active_tab

    def test_accordions(self, team, ui_teams_pg, accordions):
        '''Verify the accordions behave properly'''
        # Open edit page
        edit_pg = ui_teams_pg.open(team.id)
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
        edit_pg = ui_teams_pg.open(team.id)
        for title in accordions[:-1]:
            assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title
        assert edit_pg.accordion.get(accordions[-1])[0].is_expanded(), "The %s accordion was not expanded as expected" % accordions[-1]

    def test_edit_properties(self, team, ui_teams_pg):
        '''Verify basic form fields when editing an team'''
        edit_pg = ui_teams_pg.open(team.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access the edit region
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Modify team form fields
        edit_region.name = common.utils.random_unicode()
        edit_region.description = common.utils.random_unicode()
        edit_region.organization_name = common.utils.random_unicode()

        # Verify breadcrumb title updated
        assert edit_pg.is_the_active_breadcrumb

        # Reset Edit form
        edit_region.reset_btn.click()
        assert edit_region.name == team.name, \
            "The reset button did not restore the 'name' (%s != %s)" % \
            (edit_region.name, team.name)
        assert edit_region.description == team.description, \
            "The reset button did not restore the 'description' (%s != %s)" % \
            (edit_region.description, team.description)
        organization_name = team.get_related('organization').name
        assert edit_region.organization_name == organization_name, \
            "The reset button did not restore the 'description' (%s != %s)" % \
            (edit_region.description, organization_name)

    def test_edit_users(self, team, ui_teams_pg):
        '''Verify basic operation of teams teams accordion'''
        edit_pg = ui_teams_pg.open(team.id)
        # Access the teams region
        teams_region = edit_pg.accordion.click('Users')
        org_teams_pg = teams_region.add_btn.click()
        assert org_teams_pg.is_the_active_tab
        assert org_teams_pg.is_the_active_breadcrumb


# @pytest.mark.selenium
# @pytest.mark.nondestructive
# class Test_Teams_LowRes(Base_UI_Test):
