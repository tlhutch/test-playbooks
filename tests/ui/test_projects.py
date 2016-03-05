import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_basic_license',
        'maximized_window_size'
    )
]


def test_active_project_update(project, ui_projects):
    """Verify that the project update button is active for a scm project
    """
    assert ui_projects.table.is_displayed(), (
        'Projects table unexpectedly not displayed')

    results = ui_projects.table.query(lambda r: r['name'].text == project.name)

    assert len(results) > 0, 'Expected table data not found'

    assert results[0]['scm_update'].is_displayed(), (
        'Project update button unexpectedly not displayed')

    assert results[0]['scm_update'].is_clickable(), (
        'Project update button unexpectedly not clickable')

    assert results[0]['scm_update'].tool_tip == 'start an scm update', (
        'Unexpected project update button tooltip status message')

    # record api project last_updated date
    api_last_updated = project.last_updated

    # record ui project last_updated date
    ui_last_updated = results[0]['last_updated'].text

    # initiate SCM update
    results[0]['scm_update'].click()

    project.wait_until_completed()
    project.get()

    # TODO: add inline javascript to the page model to sample the tooltip
    # message asynchronously during the transition period.

    results = ui_projects.table.query(lambda r: r['name'].text == project.name)

    assert results[0]['scm_update'].is_clickable(), (
        'Project update button unexpectedly not clickable')

    assert results[0]['scm_update'].tool_tip == 'start an scm update', (
        'Unexpected project update button tooltip status message')

    # verify ui last_updated changed
    assert ui_last_updated != results[0]['last_updated'].text, (
        'ui project last_update value unexpectedly unchanged')

    # verify api last_updated changed
    assert api_last_updated != project.last_updated, (
        'api project last_update value unexpectedly unchanged')


@pytest.mark.skipif(True, reason='not implemented')
def test_no_pagination(authtoken, api_projects_pg, ui_projects):
    """Verify table pagination isn't present when data isn't available
    """
    if api_projects_pg.get().count > 0:
        pytest.skip("Unable to test as too many projects exist")

    assert not ui_projects.pagination.is_displayed(), (
        'Pagination unexpectedly displayed')


@pytest.mark.xfail(reason='https://github.com/ansible/ansible-tower/issues/902')
def test_edit_search_region_toggle(ui_projects_edit):
    """Verify search regions are not visible when their associated data tables
    are not populated
    """
    assert ui_projects_edit.schedules.search.is_displayed(), (
        'project schedule search region unexpectedly not displayed')

    for row in ui_projects_edit.schedules.table.rows:
        row['delete'].click().delete.click()

    assert not ui_projects_edit.schedules.search.is_displayed(), (
        'project schedule search region unexpectedly displayed')

    assert ui_projects_edit.organizations.search.is_displayed(), (
        'project organizations search region unexpectedly not displayed')

    for row in ui_projects_edit.organizations.table.rows:
        row['delete'].click().delete.click()

    assert not ui_projects_edit.organizations.search.is_displayed(), (
        'project organizations search region unexpectedly displayed')


@pytest.mark.skipif(True, reason='not implemented')
def test_inactive_project_update(project_manual, ui_projects):
    """Verify that the project update button is inactive for a manual project
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_update_project(api_projects_pg, ui_projects_edit):
    """Basic end-to-end verification for updating a project entity
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_create_project(api_projects_pg, ui_projects_add):
    """Basic end-to-end verification for creating a project entity
    """
    pass  # TODO: implement


@pytest.mark.skipif(True, reason='not implemented')
@pytest.mark.usefixtures('authtoken')
def test_delete_project(api_projects_pg, project, ui_projects):
    """Basic end-to-end verification for deleting a project
    """
    pass  # TODO: implement
