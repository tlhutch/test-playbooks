import pytest


TEST_SORT_RESOURCE_COUNT = 10


@pytest.fixture(scope='module')
def table_sort_data(v1):
    # This fixture needs to populate tower with enough data to sufficiently
    # exercise ui table sorting on all pages. The method used should be as fast
    # as possible.
    return NotImplemented


def check_table_sort(table_header):
    sort_status_options = table_header.get_sort_status_options()
    for option in sort_status_options:
        table_header.set_sort_status(option)
        assert table_header.get_sort_status() == option


skip_reason = 'faster data fixtures need to be implemented'


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_inventories(ui, table_sort_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_job_templates(ui, table_sort_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_projects(ui, table_sort_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_users(ui, table_sort_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_credentials(ui, table_sort_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_table_sort_jobs(ui, table_sort_data):
    pass
