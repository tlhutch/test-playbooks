import pytest


TEST_PAGINATION_RESOURCE_COUNT = 110


@pytest.fixture(scope='module')
def pagination_data(v1):
    # This fixture needs to populate tower with enough data to sufficiently
    # exercise ui pagination on all pages. The method used should be as fast
    # as possible.
    return NotImplemented


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


skip_reason = 'Need to implement data fixtures and redo pagination models in response to 3.1 changes'


@pytest.mark.skip(reason=skip_reason)
def test_pagination_inventories(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_job_templates(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_projects(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_organizations(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_users(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_credentials(ui, pagination_data):
    pass


@pytest.mark.skip(reason=skip_reason)
def test_pagination_jobs(ui, pagination_data):
    pass
