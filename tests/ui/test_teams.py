import pytest
import fauxfactory
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def accordions(request):
    return ('Properties', 'Credentials', 'Permissions', 'Projects', 'Users')


@pytest.fixture(scope="function", params=["Name", "Description", "Organization"])
def search_filter(request):
        return request.param


@pytest.fixture(scope="function")
def table_sort(request):
    return [('name', 'ascending'),
            ('name', 'descending'),
            ('description', 'ascending'),
            ('description', 'descending'),
            ('organization', 'ascending'),
            ('organization', 'descending')]


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Teams(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

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

        # Verify default table sort column and order
        self.assert_table_sort(ui_teams_pg.table, *table_sort[0])

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_teams_pg.table.sort_by(sorted_by, sort_order)

            # Verify table sort column and order
            self.assert_table_sort(ui_teams_pg.table, sorted_by, sort_order)

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

    def test_filter(self, team, search_filter, ui_teams_pg):
        '''Verify table filtering using a name'''
        assert ui_teams_pg.is_the_active_tab
        if search_filter.lower() == "organization":
            search_value = team.get_related(search_filter.replace(' ', '_').lower()).name
        else:
            search_value = getattr(team, search_filter.replace(' ', '_').lower())

        # search by name
        ui_teams_pg.search.search_type.select(search_filter)
        ui_teams_pg.search.search_value = search_value
        ui_teams_pg = ui_teams_pg.search.search_btn.click()

        # verify expected number of items found
        assert ui_teams_pg.pagination.total_items == 1, \
            "Unexpected number of results (%d != %d)" % \
            (ui_teams_pg.pagination.total_items, 1)
        # verify expected matching row
        assert ui_teams_pg.table.find_row(search_filter, search_value)

        # reset search filter
        ui_teams_pg = ui_teams_pg.search.reset_btn.click()
        assert ui_teams_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_teams_pg.search.search_value

    def test_filter_notfound(self, team, ui_teams_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_teams_pg.is_the_active_tab

        # search for an org that doesn't exist
        ui_teams_pg.search.search_value = fauxfactory.gen_utf8()
        ui_teams_pg = ui_teams_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_teams_pg.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_teams_pg.pagination.total_items, 0)
        assert ui_teams_pg.table.find_row("name", "No records matched your search.")

    def test_add(self, organization, ui_teams_pg):
        '''Verify basic form fields'''
        assert ui_teams_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_teams_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        add_pg.name = "Random Team - %s" % fauxfactory.gen_utf8()
        add_pg.description = "Random description - %s" % fauxfactory.gen_utf8()
        add_pg.organization_name = organization.name

        # Click Reset
        add_pg.reset_btn.click()
        assert add_pg.name == "", "Reset button did not reset the name field (value=%s)" % add_pg.name
        assert add_pg.description == "", "Reset button did not reset the description field (value=%s)" % add_pg.name
        assert add_pg.organization_name == "", "Reset button did not reset the organization_name field (value=%s)" % add_pg.name

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

    def test_edit(self, team, ui_teams_pg):
        '''Verify basic form fields when editing an team'''
        edit_pg = ui_teams_pg.open(team.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access the edit region
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Modify team form fields
        edit_region.name = fauxfactory.gen_utf8()
        edit_region.description = fauxfactory.gen_utf8()
        edit_region.organization_name = fauxfactory.gen_utf8()

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

    def test_associate_credential(self, team, ssh_credential, ui_teams_pg):
        '''Verify basic operation of adding credentials'''
        edit_pg = ui_teams_pg.open(team.id)
        region = edit_pg.accordion.click('Credentials')

        # assert disassociation
        assert region.table.find_row('name', ssh_credential.name) is None, \
            "Credential (%s) unexpectedly associated with team (%s)" % (ssh_credential.name, team.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        # filter for item
        add_pg.search.search_value = ssh_credential.name
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(name=ssh_credential.name), 'name')
        edit_pg = add_pg.select_btn.click()
        assert edit_pg.accordion.get('Credentials')[0].is_expanded(), "The credentials accordion was not expanded as expected"
        region = edit_pg.accordion.click('Credentials')

        # assert association
        assert region.table.find_row('name', ssh_credential.name) is not None, \
            "Credential (%s) was not properly associated with team (%s)" % (ssh_credential.name, team.name)

    @pytest.mark.skipif(True, reason="TODO - define a permission API fixture")
    def test_associate_permission(self, team, ui_teams_pg, permission):
        '''Verify basic operation of adding permissions'''
        edit_pg = ui_teams_pg.open(team.id)
        region = edit_pg.accordion.click('Permissions')

        # assert disassociation
        assert region.table.find_row('name', permission.name) is None, \
            "Permission (%s) unexpectedly associated with team (%s)" % (permission.name, team.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        # filter for item
        add_pg.search.search_value = permission.name
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(name=permission.name), 'name')
        edit_pg = add_pg.select_btn.click()
        assert edit_pg.accordion.get('Permissions')[0].is_expanded(), "The credentials accordion was not expanded as expected"
        region = edit_pg.accordion.click('Permissions')

        # assert association
        assert region.table.find_row('name', permission.name) is not None, \
            "Permission (%s) was not properly associated with team (%s)" % (permission.name, team.name)

    def test_associate_project(self, team, project, ui_teams_pg):
        '''Verify basic operation of adding projects'''
        edit_pg = ui_teams_pg.open(team.id)
        region = edit_pg.accordion.click('Projects')

        # assert disassociation
        assert region.table.find_row('name', project.name) is None, \
            "Project (%s) unexpectedly associated with team (%s)" % (project.name, team.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        # filter for item
        add_pg.search.search_value = project.name
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(name=project.name), 'name')
        edit_pg = add_pg.select_btn.click()
        assert edit_pg.accordion.get('Projects')[0].is_expanded(), "The credentials accordion was not expanded as expected"
        region = edit_pg.accordion.click('Projects')

        # assert association
        assert region.table.find_row('name', project.name) is not None, \
            "Project (%s) was not properly associated with team (%s)" % (project.name, team.name)

    def test_associate_user(self, team, anonymous_user, ui_teams_pg):
        '''Verify basic operation of adding users'''
        edit_pg = ui_teams_pg.open(team.id)
        region = edit_pg.accordion.click('Users')

        # assert disassociation
        assert region.table.find_row('username', anonymous_user.username) is None, \
            "User (%s) unexpectedly associated with team (%s)" % (anonymous_user.username, team.name)

        # associate
        add_pg = region.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        # filter for item
        add_pg.search.search_value = anonymous_user.username
        add_pg = add_pg.search.search_btn.click()
        add_pg.table.click_row_by_cells(dict(username=anonymous_user.username), 'username')
        edit_pg = add_pg.select_btn.click()
        assert edit_pg.accordion.get('Users')[0].is_expanded(), "The credentials accordion was not expanded as expected"
        region = edit_pg.accordion.click('Users')

        # assert association
        assert region.table.find_row('username', anonymous_user.username) is not None, \
            "User (%s) was not properly associated with team (%s)" % (anonymous_user.username, team.name)


# class Test_Teams_LowRes(Base_UI_Test):
