import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function", params=["Name", "Type", "Status"])
def search_filter(request):
        return request.param


@pytest.fixture(scope="function")
def table_sort(request):
    return [('name', 'ascending'),
            ('name', 'descending'),
            ('type', 'ascending'),
            ('type', 'descending')]


@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Projects(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_projects_pg):
        '''Verify the basics of the projects page'''
        assert ui_projects_pg.is_the_active_tab

        # FIXME - assert 'projects' table is visible (id=projects_table)
        # FIXME - assert 'projects' search box is visible (id=search-widget-container)

    def test_activity_stream(self, ui_projects_pg):
        '''Verify that the project activity stream can be open and closed'''
        # Open activity_stream
        orgs_activity_pg = ui_projects_pg.activity_stream_btn.click()
        assert orgs_activity_pg.is_the_active_tab
        assert orgs_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        orgs_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_projects_pg = orgs_activity_pg.close_btn.click()
        assert ui_projects_pg.is_the_active_tab

    def test_sort(self, many_git_projects, table_sort, ui_projects_pg):
        '''Verify table sorting'''
        assert ui_projects_pg.is_the_active_tab

        # Verify default table sort column and order
        self.assert_table_sort(ui_projects_pg.table, *table_sort[0])

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_projects_pg.table.sort_by(sorted_by, sort_order)

            # Verify table sort column and order
            self.assert_table_sort(ui_projects_pg.table, sorted_by, sort_order)

    def test_no_pagination(self, authtoken, api_projects_pg, ui_projects_pg):
        '''Verify table pagination is not present'''

        if api_projects_pg.get().count > ui_projects_pg.pagination.page_size:
            pytest.skip("Unable to test as too many projects exist")

        # Pagination present
        assert ui_projects_pg.pagination.is_displayed()
        # Pagination labels present
        assert ui_projects_pg.pagination.labels.is_displayed()
        # Pagination links shouldn't display
        assert not ui_projects_pg.pagination.links.is_displayed(), \
            "Pagination present, but fewer than %d projects are visible" % \
            ui_projects_pg.pagination.page_size

    def test_pagination(self, many_git_projects, ui_projects_pg, api_projects_pg):
        '''Verify table pagination'''

        assert ui_projects_pg.pagination.is_displayed(), "Unable to find pagination"

        # TODO: Verify expected number of items in pagination
        total_count = api_projects_pg.get().count
        total_pages = int(ceil(total_count / float(ui_projects_pg.pagination.page_size)))

        # Click next_pg until reaching the end
        curr_pg = ui_projects_pg
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

    def test_filter(self, ssh_project, search_filter, api_projects_pg, project_kind_choices, ui_projects_pg):
        '''Verify table filtering'''
        assert ui_projects_pg.is_the_active_tab
        if search_filter.lower() == "type":
            search_value = getattr(ssh_project, 'kind')
            total_items = api_projects_pg.get(kind=ssh_project.kind).count
        else:
            search_value = getattr(ssh_project, search_filter.replace(' ', '_').lower())
            total_items = 1

        # search by name
        ui_projects_pg.search.search_type.select(search_filter)
        if search_filter.lower() == "type":
            ui_projects_pg.search.search_value_select = search_value
            api_projects_pg.get(kind=ssh_project.kind).count
        else:
            ui_projects_pg.search.search_value = search_value
            ui_projects_pg = ui_projects_pg.search.search_btn.click()

        # verify expected number of items found
        assert ui_projects_pg.pagination.total_items == total_items, \
            "Unexpected number of results (%d != %d)" % \
            (ui_projects_pg.pagination.total_items, total_items)

        # verify expected matching row
        if search_filter.lower() == "type":
            assert ui_projects_pg.table.find_row(search_filter, project_kind_choices[search_value]), \
                "Unable to find table row matching (%s=%s)" % (search_filter, project_kind_choices[search_value])
        else:
            assert ui_projects_pg.table.find_row(search_filter, search_value), \
                "Unable to find table row matching (%s=%s)" % (search_filter, search_value)

        # reset search filter
        ui_projects_pg = ui_projects_pg.search.reset_btn.click()
        assert ui_projects_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_projects_pg.search.search_value

    def test_filter_notfound(self, ssh_project, ui_projects_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_projects_pg.is_the_active_tab

        # search for an org that doesn't exist
        ui_projects_pg.search.search_value = common.utils.random_unicode()
        ui_projects_pg = ui_projects_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_projects_pg.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_projects_pg.pagination.total_items, 0)
        assert ui_projects_pg.table.find_row("name", "No records matched your search.")

    def test_add(self, anonymous_user, team, ui_projects_pg):
        '''Verify basic form fields'''
        assert ui_projects_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_projects_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        assert not add_pg.save_btn.is_enabled(), "Incomplete form unexpectedly capable of submission"

        # Input Fields
        add_pg.name = common.utils.random_unicode()
        add_pg.description = common.utils.random_unicode()
        add_pg.owner = 'user'
        add_pg.user_username = anonymous_user.username
        add_pg.owner = 'team'
        add_pg.team_name = team.name
        add_pg.project_kind = 'ssh'

        # TODO ... play with more fields

        # Click Reset
        add_pg.reset_btn.click()
        fields = ('name', 'description', 'owner', 'project_kind', 'team_name')
        for field in fields:
            if field in ('owner'):
                field_value = None
            else:
                field_value = ""
            assert getattr(add_pg, field) == field_value, "Reset button did not reset the field %s='%s'" % \
                (field, getattr(add_pg, field))

    def test_project_activity_stream(self, ssh_project, ui_projects_pg):
        '''Verify that the ssh_project activity stream can be open and closed'''

        # Open edit page
        edit_pg = ui_projects_pg.open(ssh_project.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Open activity_stream
        org_activity_pg = edit_pg.activity_stream_btn.click()
        assert org_activity_pg.is_the_active_tab
        assert org_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        org_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_projects_pg = org_activity_pg.close_btn.click()
        assert ui_projects_pg.is_the_active_tab

    def test_edit(self, ssh_project, ui_projects_pg):
        '''Verify basic form fields when editing an ssh_project'''
        edit_pg = ui_projects_pg.open(ssh_project.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb
        assert edit_pg.save_btn.is_enabled(), "Completed form unexpectedly incapable of submission"

        # Modify ssh_project form fields
        edit_pg.name = common.utils.random_unicode()
        edit_pg.description = common.utils.random_unicode()
        if ssh_project.user is None:
            edit_pg.owner = 'team'
        else:
            edit_pg.owner = 'user'

        # TODO ... play with more fields

        # Verify breadcrumb title updated
        assert edit_pg.is_the_active_breadcrumb

        # Reset Edit form
        edit_pg.reset_btn.click()
        fields = ('name', 'description', 'project_kind', 'owner')
        for field in fields:
            if field in ('project_kind'):
                field_value = getattr(ssh_project, 'kind')
            elif field in ('owner'):
                if ssh_project.user is None:
                    field_value = 'team'
                else:
                    field_value = 'user'
            else:
                field_value = getattr(ssh_project, field)
            assert getattr(edit_pg, field) == field_value, "Reset button did not reset the field %s='%s'" % \
                (field, getattr(edit_pg, field))


# @pytest.mark.selenium
# @pytest.mark.nondestructive
# class Test_Projects_LowRes(Base_UI_Test):
