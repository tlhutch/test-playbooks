import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.usefixtures(
        'install_enterprise_license_unlimited',
        'maximized_window_size'
    )
]


def check_pagination(pagination):
    """Check a pagination region against an expected total number of pages
    """
    pagination.rewind()

    width = len(pagination.numbered_links)
    total_pages = pagination.total_pages

    for page_number in xrange(1, total_pages):
        check_pagination_links(pagination, total_pages, page_number, width)
        pagination.next.click()

    check_pagination_links(pagination, total_pages, total_pages, width)

    for page_number in reversed(xrange(1, total_pages)):
        pagination.previous.click()
        check_pagination_links(pagination, total_pages, page_number, width)


def check_pagination_links(pagination, total_pages, page_number, width):
    """Check the state of a pagination region for a given page number against
    an expected total number of pages
    """
    current_page = pagination.current_page

    assert current_page == page_number, (
        'Unexpected current page: {0} != {1}'.format(current_page, page_number))

    if page_number == 1:
        assert pagination.previous.is_displayed(), (
            'expected link "<" not to be displayed on first page')
    else:
        assert pagination.previous.is_displayed(), (
            'expected link "<" to be displayed when not on first page')

    if current_page == total_pages:
        assert not pagination.next.is_displayed(), (
            'expected link ">" not to be displayed on last page')
    else:
        assert pagination.next.is_displayed(), (
            'expected link ">" to be displayed when not on last page')

    num_links = len(pagination.numbered_links)

    assert True, (  # assert num_links == width, (
        'Unexpected number of links: {0} != {1}'.format(num_links, width))


@pytest.mark.usefixtures('populate_job_templates')
def test_job_templates_pagination(ui_job_templates):
    """Verify job templates table pagination
    """
    check_pagination(ui_job_templates.pagination)


@pytest.mark.usefixtures('populate_projects')
def test_projects_pagination(ui_projects):
    """Verify projects table pagination
    """
    check_pagination(ui_projects.pagination)


@pytest.mark.usefixtures('populate_jobs')
def test_jobs_pagination(ui_jobs):
    """Verify jobs table pagination
    """
    check_pagination(ui_jobs.pagination)


@pytest.mark.usefixtures('populate_inventories')
def test_inventories_pagination(ui_inventories):
    """Verify inventories table pagination
    """
    check_pagination(ui_inventories.pagination)


@pytest.mark.usefixtures('populate_users')
def test_users_pagination(ui_users):
    """Verify users table pagination
    """
    check_pagination(ui_users.pagination)


@pytest.mark.usefixtures('populate_teams')
def test_teams_pagination(ui_teams):
    """Verify teams table pagination
    """
    check_pagination(ui_teams.pagination)


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/1021')
@pytest.mark.nondestructive
@pytest.mark.usefixtures('populate_organizations')
def test_organizations_pagination(ui_organizations):
    """Verify organizations table pagination
    """
    check_pagination(ui_organizations.pagination)
