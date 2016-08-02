import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'module_install_enterprise_license',
        'max_window',
    )
]


TEST_SORT_RESOURCE_COUNT = 10


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope='module')
def table_sort_data(authtoken,  module_factories):
    synced_project = module_factories.project()
    module_factories.user()
    module_factories.job_template(project=synced_project)
    for _ in xrange(TEST_SORT_RESOURCE_COUNT - 1):
        module_factories.job_template(project=synced_project)
        # handle projects separately without scm updating
        module_factories.project(wait=False)
        # handle users
        module_factories.user()


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------

def check_table_sort(table_header):
    sort_status_options = table_header.get_sort_status_options()
    for option in sort_status_options:
        table_header.set_sort_status(option)
        assert table_header.get_sort_status() == option


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_table_sort_inventories(table_sort_data, ui_inventories):
    check_table_sort(ui_inventories.list_table.header)


def test_table_sort_job_templates(table_sort_data, ui_job_templates):
    check_table_sort(ui_job_templates.list_table.header)


def test_table_sort_projects(table_sort_data, ui_projects):
    check_table_sort(ui_projects.list_table.header)


def test_table_sort_users(table_sort_data, ui_users):
    check_table_sort(ui_users.list_table.header)


def test_table_sort_credentials(table_sort_data, ui_credentials):
    check_table_sort(ui_credentials.list_table.header)


def test_table_sort_jobs(table_sort_data, ui_jobs):
    check_table_sort(ui_jobs.jobs.table.header)
