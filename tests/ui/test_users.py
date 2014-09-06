import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def table_sort(request, admin_user, org_admin):
    return [('username', 'ascending'),
            ('username', 'descending'),
            ('first_name', 'ascending'),
            ('first_name', 'descending'),
            ('last_name', 'ascending'),
            ('last_name', 'descending')]


@pytest.fixture(scope="function")
def many_users_count(request):
    return 55


@pytest.fixture(scope="function")
def many_users(request, many_users_count, authtoken, organization, user_password):

    obj_list = list()
    for i in range(many_users_count):
        payload = dict(username="org_user_%s" % common.utils.random_ascii(),
                       first_name="Joe (%s)" % common.utils.random_unicode(),
                       last_name="User (%s)" % common.utils.random_unicode(),
                       email="org_user_%s@example.com" % common.utils.random_ascii(),
                       password=user_password,
                       organization=organization.id,)
        obj = organization.get_related('users').post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list


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
        '''Verify organiation table sorting'''
        assert ui_users_pg.is_the_active_tab

        # Verify default table sort column
        assert ui_users_pg.table.sorted_by == 'username', \
            "Unexpected default table sort column (%s != %s)" % \
            (ui_users_pg.table.sorted_by, 'username')

        # Verify default table sort order
        assert ui_users_pg.table.sort_order == 'ascending', \
            "Unexpected default table sort order (%s != %s)" % \
            (ui_users_pg.table.sort_order, 'ascending')

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_users_pg.table.sort_by(sorted_by, sort_order)

            # Verify new table sort column
            assert ui_users_pg.table.sorted_by == sorted_by, \
                "Unexpected default table sort column (%s != %s)" % \
                (ui_users_pg.table.sorted_by, sorted_by)

            # Verify new table sort order
            assert ui_users_pg.table.sort_order == sort_order, \
                "Unexpected default table sort order (%s != %s)" % \
                (ui_users_pg.table.sort_order, sort_order)

    def test_no_pagination(self, authtoken, api_users_pg, api_default_page_size, ui_users_pg):
        '''Verify organiation table pagination is not present'''

        if api_users_pg.get().count > api_default_page_size:
            pytest.skip("Unable to test as too many users exist")

        assert not ui_users_pg.pagination.is_displayed(), \
            "Pagination present, but fewer than %d users are visible" % \
            api_default_page_size

    def test_pagination(self, many_users, ui_users_pg, api_users_pg, ui_default_page_size):
        '''Verify organiation table pagination'''

        assert ui_users_pg.pagination.is_displayed(), "Unable to find pagination"

        # TODO: Verify expected number of items in pagination
        total_count = api_users_pg.get().count
        total_pages = int(ceil(total_count / float(ui_default_page_size)))

        # Assert expected pagination links
        assert ui_users_pg.pagination.current_page == 1, \
            "Unexpected current page number (%d != %d)" % \
            (ui_users_pg.pagination.current_page, 1)
        assert not ui_users_pg.pagination.first_page.is_displayed()
        assert not ui_users_pg.pagination.prev_page.is_displayed()
        assert ui_users_pg.pagination.next_page.is_displayed()
        assert not ui_users_pg.pagination.last_page.is_displayed()
        assert ui_users_pg.pagination.count == total_pages, \
            "Unexpected number of pagination links (%d != %d)" % \
            (ui_users_pg.pagination.count, total_pages)

        # Click next_page
        next_pg = ui_users_pg.pagination.next_page.click()

        # Assert expected pagination links
        assert next_pg.pagination.current_page == 2, \
            "Unexpected current page number (%d != %d)" % \
            (next_pg.pagination.current_page, 2)
        assert not next_pg.pagination.first_page.is_displayed()
        assert next_pg.pagination.prev_page.is_displayed()
        assert next_pg.pagination.next_page.is_displayed()
        assert not next_pg.pagination.last_page.is_displayed()
        assert next_pg.pagination.count == total_pages, \
            "Unexpected number of pagination links (%d != %d)" % \
            (next_pg.pagination.count, total_pages)

        # Click prev_page
        prev_pg = next_pg.pagination.prev_page.click()

        # Assert expected pagination links
        assert prev_pg.pagination.current_page == 1, \
            "Unexpected current page number (%d != %d)" % \
            (prev_pg.pagination.current_page, 1)
        assert not prev_pg.pagination.first_page.is_displayed()
        assert prev_pg.pagination.prev_page.is_displayed()
        assert not prev_pg.pagination.next_page.is_displayed()
        assert not prev_pg.pagination.last_page.is_displayed()
        assert prev_pg.pagination.count == total_pages, \
            "Unexpected number of pagination links (%d != %d)" % \
            (prev_pg.pagination.count, total_pages)

        # TODO: Click page#2

    def test_filter_name(self, user, ui_users_pg):
        '''Verify organiation table filtering using a name'''
        assert ui_users_pg.is_the_active_tab

        # search by name
        ui_users_pg.search.search_type.select("Name")
        ui_users_pg.search.search_value = user.name
        ui_users_pg = ui_users_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_users_pg.pagination.total_items == 1
        num_rows = len(list(ui_users_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_users_pg.table.find_row("name", user.name)

        # reset search filter
        ui_users_pg = ui_users_pg.search.reset_btn.click()
        assert ui_users_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_users_pg.search.search_value

    def test_filter_description(self, user, ui_users_pg):
        '''Verify organiation table filtering using a description'''
        assert ui_users_pg.is_the_active_tab

        # search by description
        ui_users_pg.search.search_type.select("Description")
        ui_users_pg.search.search_value = user.description
        ui_users_pg = ui_users_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_users_pg.pagination.total_items == 1
        num_rows = len(list(ui_users_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_users_pg.table.find_row("description", user.description)

        # reset search filter
        ui_users_pg = ui_users_pg.search.reset_btn.click()
        assert ui_users_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_users_pg.search.search_value

    def test_filter_notfound(self, user, ui_users_pg):
        '''Verify organiation table filtering using a bogus value'''
        assert ui_users_pg.is_the_active_tab

        # Search for an org that doesn't exist
        ui_users_pg.search.search_type.select("Name")
        ui_users_pg.search.search_value = common.utils.random_unicode()
        ui_users_pg = ui_users_pg.search.search_btn.click()

        # TODO: verify expected number of items found
        # assert ui_users_pg.pagination.total_items == 1
        num_rows = len(list(ui_users_pg.table.rows))
        assert num_rows == 1, "Unexpected number of results found (%d != %d)" % (num_rows, 1)
        assert ui_users_pg.table.find_row("name", "No records matched your search.")

    def test_add(self, ui_users_pg):
        '''Verify basic organiation form fields'''
        assert ui_users_pg.add_btn, "Unable to locate add button"

        # Click Add button
        add_pg = ui_users_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb

        # Input Fields
        add_pg.name = "Random User - %s" % common.utils.random_unicode()
        add_pg.description = "Random description - %s" % common.utils.random_unicode()

        # Click Reset
        add_pg.reset_btn.click()
        assert add_pg.name == "", "Reset button did not reset the field: name"
        assert add_pg.description == "", "Reset button did not reset the field: description"

    def test_org_activity_stream(self, user, ui_users_pg):
        '''Verify that the user activity stream can be open and closed'''

        # Open edit page
        edit_pg = ui_users_pg.open(user.id)
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

    def test_accordions(self, ui_users_pg, user):
        '''Verify the organiation accordions behave properly'''
        # Open edit page
        edit_pg = ui_users_pg.open(user.id)
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
        edit_pg = ui_users_pg.open(user.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.accordion.get('Properties')[0].is_collapsed(), "The properties accordion was not collapse as expected"
        assert edit_pg.accordion.get('Users')[0].is_expanded(), "The users accordion was not expand as expected"
        assert edit_pg.accordion.get('Administrators')[0].is_collapsed(), "The administrators accordion was not collapse as expected"

    def test_edit_properties(self, ui_users_pg, user):
        '''Verify basic organiation form fields when editing an user'''
        edit_pg = ui_users_pg.open(user.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access the edit region
        edit_region = edit_pg.accordion.get('Properties')[1]

        # Modify user form fields
        edit_region.name = common.utils.random_unicode()
        edit_region.description = common.utils.random_unicode()

        # Verify breadcrumb title updated
        assert edit_pg.is_the_active_breadcrumb

        # Reset Edit form
        edit_region.reset_btn.click()
        assert edit_pg.is_the_active_breadcrumb
        assert edit_region.name == user.name, \
            "The reset button did not restore the 'name' (%s != %s)" % \
            (edit_region.name, user.name)
        assert edit_region.description == user.description, \
            "The reset button did not restore the 'description' (%s != %s)" % \
            (edit_region.description, user.description)

    def test_edit_users(self, ui_users_pg, user):
        '''Verify basic operation of users users accordion'''
        edit_pg = ui_users_pg.open(user.id)
        # Access the users region
        users_region = edit_pg.accordion.click('Users')
        org_users_pg = users_region.add_btn.click()
        assert org_users_pg.is_the_active_tab
        assert org_users_pg.is_the_active_breadcrumb

    def test_edit_admins(self, ui_users_pg, user):
        '''Verify basic operation of users admins accordion'''
        edit_pg = ui_users_pg.open(user.id)
        # Access the users region
        admins_region = edit_pg.accordion.click('Administrators')
        org_admins_pg = admins_region.add_btn.click()
        assert org_admins_pg.is_the_active_tab
        assert org_admins_pg.is_the_active_breadcrumb


# @pytest.mark.selenium
# @pytest.mark.nondestructive
# class Test_Users_LowRes(Base_UI_Test):
