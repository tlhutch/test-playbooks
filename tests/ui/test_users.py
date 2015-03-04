import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def accordions(request):
    return ('Properties', 'Credentials', 'Permissions', 'Admin of Organizations', 'Organizations', 'Teams')


@pytest.fixture(scope="function", params=["Username", "First Name", "Last Name"])
def search_filter(request):
    return request.param


@pytest.fixture(scope="function")
def table_sort(request):
    return [('username', 'ascending'),
            ('username', 'descending'),
            ('first_name', 'ascending'),
            ('first_name', 'descending'),
            ('last_name', 'ascending'),
            ('last_name', 'descending')]


@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class Test_Users(Base_UI_Test):

    pytestmark = pytest.mark.usefixtures('maximized', 'backup_license', 'install_license_unlimited')

    def test_active_tab(self, ui_users_pg):
        '''Verify the basics of the users page'''
        assert ui_users_pg.is_the_active_tab

        # FIXME - assert 'users' table is visible (id=users_table)
        # FIXME - assert 'users' search box is visible (id=search-widget-container)

    def test_activity_stream(self, ui_users_pg):
        '''Verify that the user activity stream can be open and closed'''
        # Open activity_stream
        orgs_activity_pg = ui_users_pg.activity_stream_btn.click()
        assert orgs_activity_pg.is_the_active_tab
        assert orgs_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        orgs_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_users_pg = orgs_activity_pg.close_btn.click()
        assert ui_users_pg.is_the_active_tab

    def test_sort(self, many_users, table_sort, ui_users_pg):
        '''Verify table sorting'''
        assert ui_users_pg.is_the_active_tab

        # Verify default table sort column and order
        self.assert_table_sort(ui_users_pg.table, *table_sort[0])

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_users_pg.table.sort_by(sorted_by, sort_order)
            self.assert_table_sort(ui_users_pg.table, sorted_by, sort_order)

    def test_no_pagination(self, authtoken, api_users_pg, ui_users_pg):
        '''Verify table pagination is not present'''

        if api_users_pg.get().count > ui_users_pg.pagination.page_size:
            pytest.skip("Unable to test as too many users exist")

        # Pagination present
        assert ui_users_pg.pagination.is_displayed()
        # Pagination labels present
        assert ui_users_pg.pagination.labels.is_displayed()
        # Pagination links shouldn't display
        assert not ui_users_pg.pagination.links.is_displayed(), \
            "Pagination present, but fewer than %d users are visible" % \
            ui_users_pg.pagination.page_size

    def test_pagination(self, many_users, ui_users_pg, api_users_pg):
        '''Verify table pagination'''

        assert ui_users_pg.pagination.is_displayed(), "Unable to find pagination"

        # assert total_items
        total_items = api_users_pg.get().count
        assert total_items == ui_users_pg.pagination.total_items, \
            "The API and the UI differ on the total paginated items (%s != %s)" % \
            (total_items, ui_users_pg.pagination.total_items)

        # assert total_pages
        total_pages = int(ceil(total_items / float(ui_users_pg.pagination.page_size)))
        assert total_pages == ui_users_pg.pagination.total_pages, \
            "The API and the UI differ on the total number of pages (%s != %s)" % \
            (total_pages, ui_users_pg.pagination.total_pages)

        # click next_pg until reaching the end
        curr_pg = ui_users_pg
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

        # click prev_pg until reaching the beginning
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

    def test_filter(self, anonymous_user, search_filter, ui_users_pg):
        '''Verify table filtering using a name'''
        assert ui_users_pg.is_the_active_tab
        search_value = getattr(anonymous_user, search_filter.replace(' ', '_').lower())

        # search by username
        ui_users_pg.search.search_type.select(search_filter)
        ui_users_pg.search.search_value = search_value
        ui_users_pg = ui_users_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_users_pg.pagination.total_items == 1, \
            "Unexpected number of results (%d != %d)" % \
            (ui_users_pg.pagination.total_items, 1)
        # assert desired item
        assert ui_users_pg.table.find_row(search_filter, search_value)

        # reset search filter
        ui_users_pg = ui_users_pg.search.reset_btn.click()
        assert ui_users_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_users_pg.search.search_value

    def test_filter_notfound(self, anonymous_user, ui_users_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_users_pg.is_the_active_tab

        # search for an org that doesn't exist
        ui_users_pg.search.search_value = common.utils.random_unicode()
        ui_users_pg = ui_users_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_users_pg.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_users_pg.pagination.total_items, 0)
        # assert failed match string
        assert ui_users_pg.table.find_row("username", "No records matched your search.")

    def test_add(self, ui_users_pg):
        '''Verify basic form fields'''
        assert ui_users_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_users_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        fields = ('first_name', 'last_name', 'username', 'email', 'password',
                  'password_confirm', 'is_superuser', 'organization_name')
        for field in fields:
            if field in ('is_superuser'):
                setattr(add_pg, field, True)
            else:
                setattr(add_pg, field, common.utils.random_unicode())

        # Click Reset
        add_pg.reset_btn.click()

        # assert reset
        for field in fields:
            if field in ('is_superuser'):
                field_value = False
            else:
                field_value = ""
            assert getattr(add_pg, field) == field_value, "Reset button did not reset the field %s='%s'" % \
                (field, getattr(add_pg, field))

    def test_user_activity_stream(self, anonymous_user, ui_users_pg):
        '''Verify that the user activity stream can be open and closed'''

        # Open edit page
        edit_pg = ui_users_pg.open(anonymous_user.id)
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
        ui_users_pg = org_activity_pg.close_btn.click()
        assert ui_users_pg.is_the_active_tab

    def test_accordions(self, anonymous_user, ui_users_pg, accordions):
        '''Verify the accordions behave properly'''
        # Open edit page
        edit_pg = ui_users_pg.open(anonymous_user.id)
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
        edit_pg = ui_users_pg.open(anonymous_user.id)
        for title in accordions[:-1]:
            assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title
        assert edit_pg.accordion.get(accordions[-1])[0].is_expanded(), "The %s accordion was not expanded as expected" % accordions[-1]

    def test_edit(self, anonymous_user, ui_users_pg):
        '''Verify basic form fields when editing an user'''
        edit_pg = ui_users_pg.open(anonymous_user.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access the edit region
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Modify Fields
        fields = ('first_name', 'last_name', 'username', 'email', 'password',
                  'password_confirm', 'is_superuser')
        for field in fields:
            if field in ('is_superuser'):
                setattr(edit_region, field, not anonymous_user.is_superuser)
            else:
                setattr(edit_region, field, common.utils.random_unicode())

        # Click Reset
        edit_region.reset_btn.click()

        # assert reset
        for field in fields:
            if field in ('password', 'password_confirm'):
                field_value = ''
            else:
                field_value = getattr(anonymous_user, field)
            assert getattr(edit_region, field) == field_value, \
                "Reset button did not reset the field %s (actual:'%s', expected:'%s')" % \
                (field, getattr(edit_region, field), field_value)

    def test_associate_credential(self, anonymous_user, ssh_credential, ui_users_pg):
        '''Verify basic operation of adding credentials'''
        edit_pg = ui_users_pg.open(anonymous_user.id)
        region = edit_pg.accordion.click('Credentials')

        # assert disassociation
        assert region.table.find_row('name', ssh_credential.name) is None, \
            "Credential (%s) unexpectedly associated with user (%s)" % (ssh_credential.name, anonymous_user.name)

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
            "Credential (%s) was not properly associated with user (%s)" % (ssh_credential.name, anonymous_user.name)

    @pytest.mark.skipif(True, reason="TODO - define a permission API fixture")
    def test_associate_permission(self, anonymous_user, ui_users_pg):
        '''Verify basic operation of adding permissions'''
        edit_pg = ui_users_pg.open(anonymous_user.id)
        region = edit_pg.accordion.click('Permissions')

        # assert disassociation
        assert region.table.find_row('name', permission.name) is None, \
            "Permission (%s) unexpectedly associated with user (%s)" % \
            (permission.name, anonymous_user.name)

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
            "Permission (%s) was not properly associated with user (%s)" % (permission.name, anonymous_user.name)

    def test_associate_project(self, anonymous_user, project, ui_users_pg):
        '''Verify basic operation of adding projects'''
        edit_pg = ui_users_pg.open(anonymous_user.id)
        region = edit_pg.accordion.click('Projects')

        # assert disassociation
        assert region.table.find_row('name', project.name) is None, \
            "Project (%s) unexpectedly associated with user (%s)" % (project.name, anonymous_user.name)

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
            "Project (%s) was not properly associated with user (%s)" % (project.name, anonymous_user.name)


# @pytest.mark.nondestructive
# class Test_Users_LowRes(Base_UI_Test):
