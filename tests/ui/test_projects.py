import json
import pytest
import common.utils
from math import ceil
from tests.ui import Base_UI_Test


@pytest.fixture(scope="function")
def accordions(request):
    return ('Properties', 'Organizations', 'Schedules')


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

    def test_filter(self, project, search_filter, api_projects_pg, project_scm_type_choices, project_status_choices, ui_projects_pg):
        '''Verify table filtering'''
        assert ui_projects_pg.is_the_active_tab

        # determine expected search results
        if search_filter.lower() == "type":
            search_value = getattr(project, 'scm_type')
            total_items = api_projects_pg.get(scm_type=project.scm_type).count
        elif search_filter.lower() == "status":
            search_value = getattr(project, 'status')
            total_items = api_projects_pg.get(status=project.status).count
        else:
            search_value = getattr(project, search_filter.replace(' ', '_').lower())
            total_items = 1

        # perform search
        ui_projects_pg.search.search_type.select(search_filter)
        if search_filter.lower() in ('type', 'status'):
            ui_projects_pg.search.search_value_select = search_value
            # api_projects_pg.get(scm_type=project.scm_type).count
        else:
            ui_projects_pg.search.search_value = search_value
            ui_projects_pg = ui_projects_pg.search.search_btn.click()

        # assert expected number of items
        assert ui_projects_pg.pagination.total_items == total_items, \
            "Unexpected number of results (%d != %d)" % \
            (ui_projects_pg.pagination.total_items, total_items)

        # assert expected matching row
        if search_filter.lower() == "type":
            assert ui_projects_pg.table.find_row(search_filter, project_scm_type_choices[search_value]), \
                "Unable to find table row matching (%s=%s)" % (search_filter, project_scm_type_choices[search_value])
        elif search_filter.lower() == "status":
            myrow = ui_projects_pg.table.find_row('name', project.name)
            assert myrow, "Unable to find table row matching (%s=%s)" % ('name', project.name)
            assert myrow.status.value == project_status_choices[search_value], \
                "Unexpected status column (%s != %s)" % \
                (myrow.status.value, project_status_choices[search_value])
        else:
            assert ui_projects_pg.table.find_row(search_filter, search_value), \
                "Unable to find table row matching (%s=%s)" % (search_filter, search_value)

        # reset search filter
        ui_projects_pg = ui_projects_pg.search.reset_btn.click()

        # assert empty search_value
        assert ui_projects_pg.search.search_value == '', \
            "search_value did not reset (%s)" % \
            ui_projects_pg.search.search_value

    def test_filter_notfound(self, project, ui_projects_pg):
        '''Verify table filtering using a bogus value'''
        assert ui_projects_pg.is_the_active_tab

        # search for an object that doesn't exist
        ui_projects_pg.search.search_value = common.utils.random_unicode()
        ui_projects_pg = ui_projects_pg.search.search_btn.click()

        # assert expected number of items found
        assert ui_projects_pg.pagination.total_items == 0, \
            "Unexpected number of results (%d != %d)" % \
            (ui_projects_pg.pagination.total_items, 0)
        assert ui_projects_pg.table.find_row("status", "No records matched your search.")

    def test_add(self, organization, ui_projects_pg):
        '''Verify basic form fields'''
        assert ui_projects_pg.add_btn, "Unable to locate add button"

        # click add
        add_pg = ui_projects_pg.add_btn.click()
        assert add_pg.is_the_active_tab
        assert add_pg.is_the_active_breadcrumb
        assert not add_pg.save_btn.is_enabled(), "Incomplete form unexpectedly capable of submission"
        assert add_pg.scm_type == '', "Unexpected default value for scm_type ('%s' != '%s')" % ('', add_pg.scm_type)

        # update form fields
        add_pg.name = common.utils.random_unicode()
        add_pg.description = common.utils.random_unicode()
        add_pg.organization_name = organization.name
        add_pg.scm_type = 'git'
        add_pg.scm_clean = True
        add_pg.scm_delete_on_update = True
        add_pg.scm_update_on_launch = True

        # TODO ... play with more fields

        # click reset
        add_pg.reset_btn.click()

        # assert form values reset
        checkboxes = ('scm_clean', 'scm_delete_on_update', 'scm_update_on_launch')
        fields = ('name', 'description', 'organization_name', 'scm_type') + checkboxes
        for field in fields:
            if field in checkboxes:
                field_value = False
            else:
                field_value = ""
            assert getattr(add_pg, field) == field_value, "Reset button did not reset the field %s='%s'" % \
                (field, getattr(add_pg, field))

    def test_project_activity_stream(self, project, ui_projects_pg):
        '''Verify that the project activity stream can be open and closed'''

        # Open edit page
        edit_pg = ui_projects_pg.open(project.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # Access properties accordion
        properties_rg = edit_pg.accordion.click('Properties')
        # Open activity_stream
        org_activity_pg = properties_rg.activity_stream_btn.click()
        assert org_activity_pg.is_the_active_tab
        assert org_activity_pg.is_the_active_breadcrumb

        # Refresh activity_stream
        org_activity_pg.refresh_btn.click()

        # Close activity_stream
        ui_projects_pg = org_activity_pg.close_btn.click()
        assert ui_projects_pg.is_the_active_tab

    def test_project_update_btn(self, project, project_status_choices, ui_projects_pg):
        '''Verify that the project activity stream can be open and closed'''

        # open edit page
        edit_pg = ui_projects_pg.open(project.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb

        # access properties accordion
        properties_rg = edit_pg.accordion.click('Properties')
        # record project last_updated date
        last_updated = project.last_updated
        # initiate SCM update
        projects_pg = properties_rg.scm_update_btn.click()
        assert projects_pg.is_the_active_tab

        # FIXME - filter for the desired project
        if False:
            # filter for desired project
            projects_pg.search.search_value = project.name
            projects_pg = projects_pg.search.search_btn.click()

            # assert expected number of items found
            assert projects_pg.pagination.total_items == 1, \
                "Unexpected number of results (%d != %d)" % \
                (projects_pg.pagination.total_items, 1)

        # wait for project update to start
        project = project.wait_until_started()
        # assert correct project status icon
        # FIXME - sometimes the API says running, but the UI shows 'icon-job-none'
        project_status = projects_pg.table.find_row('name', project.name).status.value
        assert project_status == project_status_choices['running'], \
            "Unexpected project status (%s != %s)" % \
            (project_status, project_status_choices['running'])

        # wait for project update to complete
        project.get_related('current_update').wait_until_completed()
        # assert correct project status icon
        project_status = projects_pg.table.find_row('name', project.name).status.value
        assert project_status == project_status_choices['successful'], \
            "Unexpected project status (%s != %s)" % \
            (project_status, project_status_choices['successful'])

        # assert last_updated changed
        project.get()
        assert last_updated != project.last_updated, "Project update not triggered, last_update did not change ('%s')" % project.last_updated

        # FIXME - assert last_updated column == project.last_updated

    def test_edit(self, project, ui_projects_pg):
        '''Verify basic form fields when editing an project'''
        edit_pg = ui_projects_pg.open(project.id)
        assert edit_pg.is_the_active_tab
        assert edit_pg.is_the_active_breadcrumb
        assert edit_pg.save_btn.is_enabled(), "Completed form unexpectedly incapable of submission"

        # Modify project form fields
        edit_pg.name = common.utils.random_unicode()
        edit_pg.description = common.utils.random_unicode()

        # TODO ... play with more fields

        # assert breadcrumb title updated
        assert edit_pg.is_the_active_breadcrumb

        # assert form cannot be saved
        edit_pg.scm_type = ''
        assert not edit_pg.save_btn.is_enabled(), "Incomplete form unexpectedly capable of submission"
        edit_pg.scm_type = project.scm_type
        assert edit_pg.save_btn.is_enabled(), "Completed form unexpectedly incapable of submission"

        # Reset Edit form
        edit_pg.reset_btn.click()
        checkboxes = ('scm_clean', 'scm_delete_on_update', 'scm_update_on_launch')
        fields = ('name', 'description', 'scm_type', 'scm_url', 'scm_branch') + checkboxes

        for field in fields:
            if field in checkboxes:
                field_value = getattr(project, field)
            else:
                field_value = getattr(project, field)
            assert getattr(edit_pg, field) == field_value, "Reset button did not reset the field %s='%s'" % \
                (field, getattr(edit_pg, field))

    def test_accordions(self, project, ui_projects_pg, accordions):
        '''Verify the accordions behave properly'''
        # Open edit page
        edit_pg = ui_projects_pg.open(project.id)
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
        edit_pg = ui_projects_pg.open(project.id)
        for title in accordions[:-1]:
            assert edit_pg.accordion.get(title)[0].is_collapsed(), "The %s accordion was not collapsed as expected" % title
        assert edit_pg.accordion.get(accordions[-1])[0].is_expanded(), "The %s accordion was not expanded as expected" % accordions[-1]

# @pytest.mark.selenium
# @pytest.mark.nondestructive
# class Test_Projects_LowRes(Base_UI_Test):
