import pytest

PAGINATED_RESOURCE_COUNT = 110

pytestmark = [
    pytest.mark.ui,
    pytest.mark.pagination,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
        'max_window',
    )
]


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope='module')
def pagination_data(authtoken,  module_factories):
    synced_project = module_factories.project()
    module_factories.user()
    module_factories.job_template(project=synced_project)
    for _ in xrange(PAGINATED_RESOURCE_COUNT - 1):
        module_factories.job_template(project=synced_project)
        # handle projects separately without scm updating
        module_factories.project(wait=False)
        # handle users
        module_factories.user()


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------

def check_pagination(pagination):
    pagination.reset()
    total_pages = pagination.total_pages
    # check the currently displayed active link
    assert int(pagination.active.text) == 1
    assert pagination.current_page == 1
    for n, _ in enumerate(pagination.scan_right()):
        expected_page = n + 2
        # check that that currently displayed page number corresponds
        # to the number of pages we've clicked through
        assert pagination.current_page == expected_page
        # check the currently displayed active link
        assert int(pagination.active.text) == expected_page
        # check that "<" is visible
        assert pagination('<').is_displayed()
        # check that the displayed total number of pages does not change
        assert pagination.total_pages == total_pages
    # check the currently displayed active link
    assert int(pagination.active.text) == total_pages
    # check that ">" isn't visible on the last page
    assert not pagination('>').is_displayed()
    # check "ITEMS X-Y OF Z" label
    assert pagination.item_range[1] == pagination.total_items
    for n, _ in enumerate(pagination.scan_left()):
        expected_page = total_pages - (n + 1)
        # check that that currently displayed page number corresponds
        # to the number of pages we've clicked through
        assert pagination.current_page == expected_page
        # check the currently displayed active link
        assert int(pagination.active.text) == expected_page
        # check that ">" is visible
        assert pagination('>').is_displayed()
        # check that the displayed total number of pages does not change
        assert pagination.total_pages == total_pages


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_pagination_inventories(pagination_data, ui_inventories):
    check_pagination(ui_inventories.list_pagination)


def test_pagination_job_templates(pagination_data, ui_job_templates):
    check_pagination(ui_job_templates.list_pagination)


def test_pagination_projects(pagination_data, ui_projects):
    check_pagination(ui_projects.list_pagination)


def test_pagination_organizations(pagination_data, ui_organizations):
    check_pagination(ui_organizations.list_pagination)


def test_pagination_users(pagination_data, ui_users):
    check_pagination(ui_users.list_pagination)


def test_pagination_credentials(pagination_data, ui_credentials):
    check_pagination(ui_credentials.list_pagination)


def test_pagination_jobs(pagination_data, ui_jobs):
    check_pagination(ui_jobs.list_pagination)
