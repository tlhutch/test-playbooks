import pytest
import urllib
from math import ceil
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from common.utils import random_utf8


@pytest.mark.skipif(True, reason='Needs to be updated with 3.0 page models')
class Test_Portal(object):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

    def test_account_menu(self, ui_portal_pg):
        '''Verify the Portal page account_menu links behave as expected.'''

        # assert portal mode is the active tab
        assert ui_portal_pg.is_the_active_tab

        # exit portal mode
        dashboard_pg = ui_portal_pg.account_menu.click('Exit Portal')

        # assert the dashboard is the active tab
        assert dashboard_pg.is_the_active_tab

    def test_redirect_after_first_login(self, mozwebqa):
        '''
        Verify a that accessing Tower for the first time, using the
        /#/portal URL, redirects to the portal page after successful login.
        '''

        # TODO: it'd be nice to have a fixture that returns the page object,
        # but does *not* login.  The 'ui_portal_pg' fixture does support
        # 'fixture_args', but I'm not happy with how that's currently
        # implemented.  We may use this in the future after some
        # cleanup+adjustment.  Sample usage included below:
        #   @pytest.mark.fixture_args(login=False)
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


@pytest.fixture(scope="function", params=["Name", "Description"])
def search_filter(request):
    return request.param


@pytest.fixture(scope="function")
def table_sort(request):
    return [('name', 'ascending'),
            ('name', 'descending'),
            ('description', 'ascending'),
            ('description', 'descending')]


@pytest.fixture(scope="function")
def many_job_templates(request, api_job_templates_pg, job_template):
    obj_list = list()
    for i in range(55):
        payload = job_template.json
        payload.update(dict(name="job_template-%s" % random_utf8(),
                            description="Random job_template with machine credentials - %s" % random_utf8()))
        obj = api_job_templates_pg.post(payload)
        request.addfinalizer(obj.delete)
        obj_list.append(obj)
    return obj_list


@pytest.mark.skipif(True, reason='Needs to be updated with 3.0 page models')
class Test_Portal_Job_Templates(object):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')
    # search_filters = ('Name', 'Description')
    # table_sort = [('name', 'ascending'),
    #               ('name', 'descending'),
    #               ('description', 'ascending'),
    #               ('description', 'descending')]

    def test_sort(self, many_job_templates, table_sort, ui_portal_pg):
        '''Verify table sorting'''
        assert ui_portal_pg.is_the_active_tab

        # Verify default table sort column and order
        self.assert_table_sort(ui_portal_pg.job_templates.table, *table_sort[0])

        for sorted_by, sort_order in table_sort:
            # Change table sort
            ui_portal_pg.job_templates.table.sort_by(sorted_by, sort_order)

            # Verify table sort column and order
            self.assert_table_sort(ui_portal_pg.job_templates.table, sorted_by, sort_order)

    def test_no_pagination(self, authtoken, api_job_templates_pg, ui_portal_pg):
        '''Verify table pagination is not present'''

        if api_job_templates_pg.get().count > ui_portal_pg.job_templates.pagination.page_size:
            pytest.skip("Unable to test as too many job_templates exist")

        # Pagination present
        assert ui_portal_pg.job_templates.pagination.is_displayed()
        # Pagination labels present
        assert ui_portal_pg.job_templates.pagination.labels.is_displayed()
        # Pagination links shouldn't display
        assert not ui_portal_pg.job_templates.pagination.links.is_displayed(), \
            "Pagination present, but fewer than %d job_templates are visible" % \
            ui_portal_pg.job_templates.pagination.page_size

    def test_pagination(self, many_job_templates, ui_portal_pg, api_job_templates_pg):
        '''Verify table pagination'''

        assert ui_portal_pg.job_templates.pagination.is_displayed(), "Unable to find pagination"

        # assert total_items
        total_items = api_job_templates_pg.get().count
        assert total_items == ui_portal_pg.job_templates.pagination.total_items, \
            "The API and the UI differ on the total paginated items (%s != %s)" % \
            (total_items, ui_portal_pg.job_templates.pagination.total_items)

        # assert total_pages
        total_pages = int(ceil(total_items / float(ui_portal_pg.job_templates.pagination.page_size)))
        assert total_pages == ui_portal_pg.job_templates.pagination.total_pages, \
            "The API and the UI differ on the total number of pages (%s != %s)" % \
            (total_pages, ui_portal_pg.job_templates.pagination.total_pages)

        # click next_pg until reaching the end
        curr_pg = ui_portal_pg.job_templates
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

    def test_filter(self, job_template, search_filter, api_job_templates_pg, ui_portal_pg):
        '''Verify table filtering'''
        assert ui_portal_pg.is_the_active_tab

        # determine expected search results
        search_value = getattr(job_template, search_filter.replace(' ', '_').lower())
        total_items = 1

        # perform search
        ui_portal_pg.job_templates.search.search_type.select(search_filter)
        if search_filter.lower() in ('type', 'status'):
            ui_portal_pg.job_templates.search.search_value_select = search_value
            # api_job_templates_pg.get(scm_type=job_template.scm_type).count
        else:
            ui_portal_pg.job_templates.search.search_value = search_value
            ui_portal_pg = ui_portal_pg.job_templates.search.search_btn.click()

        # assert expected number of items
        assert ui_portal_pg.job_templates.pagination.total_items == total_items, \
            "Unexpected number of results (%d != %d)" % \
            (ui_portal_pg.job_templates.pagination.total_items, total_items)

        # assert expected matching row
        assert ui_portal_pg.job_templates.table.find_row(search_filter, search_value), \
            "Unable to find table row matching (%s=%s)" % (search_filter, search_value)

        # reset search filter
        ui_portal_pg = ui_portal_pg.job_templates.search.reset_btn.click()

        # assert empty search_value
        assert ui_portal_pg.job_templates.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_portal_pg.job_templates.search.search_value

    def test_filter_notfound(self, job_template, ui_portal_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_portal_pg.is_the_active_tab

        # search for an object that doesn't exist
        ui_portal_pg.job_templates.search.search_value = random_utf8()
        ui_portal_pg = ui_portal_pg.job_templates.search.search_btn.click()

        # assert expected number of items found
        assert ui_portal_pg.job_templates.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_portal_pg.job_templates.pagination.total_items, 0)
        assert ui_portal_pg.job_templates.table.find_row("name", "No records matched your search.")

    def test_job_template_launch(self, job_template_ping, job_status_choices, ui_portal_pg):
        '''Verify expected behavior when launching a job_template within portal mode.'''
        assert ui_portal_pg.is_the_active_tab

        # search for the desired job_template
        ui_portal_pg.job_templates.search.search_value = job_template_ping.name
        ui_portal_pg = ui_portal_pg.job_templates.search.search_btn.click()

        # assert expected matching row
        match_row = ui_portal_pg.job_templates.table.find_row('name', job_template_ping.name)
        assert match_row, "Unable to find table row matching (%s=%s)" % \
            ('name', job_template_ping.name)

        # launch job_template
        ui_portal_pg = match_row.launch.click('submit-action')

        # assert the portal page is still active
        assert ui_portal_pg.is_the_active_tab

        # FIXME - filter the jobs region for the desired job

        # wait for job to start
        job_template_ping = job_template_ping.wait_until_started()

        # assert correct job status icon
        match_row = ui_portal_pg.jobs.table.find_row('name', job_template_ping.name)
        assert match_row.status.value == job_status_choices['pending'], \
            "Unexpected job status (%s != %s)" % \
            (match_row.status.value, job_status_choices['pending'])

        # wait for job to complete
        job_template_ping = job_template_ping.wait_until_completed()

        # assert correct job status icon
        match_row = ui_portal_pg.jobs.table.find_row('name', job_template_ping.name)
        assert match_row.status.value == job_status_choices['successful'], \
            "Unexpected job status (%s != %s)" % \
            (match_row.status.value, job_status_choices['successful'])


@pytest.mark.skipif(True, reason='Needs to be updated with 3.0 page models')
class Test_Portal_Jobs(object):

    pytestmark = pytest.mark.usefixtures('maximized', 'install_license_unlimited')

    def test_jobs_only_includes_playbook_runs(self):
        '''Verify a that jobs region only shows jobs of type=playbook_run'''

    def test_job_details(self):
        '''Verify expected behavior when launching a job_template within portal mode.'''
