import pytest

pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'install_enterprise_license_unlimited',
        'maximized_window_size'
    )
]


def check_table_sort(table):
    """Verify table column sort order
    """
    assert table.header.is_displayed(), 'Expected table header to be visible'

    for column_name in table.sortable_column_names:
        for sort_order in table.header._sort_status.values():
            column_sort_order = (column_name, sort_order)

            table.set_column_sort_order(column_sort_order)
            actual_column_sort_order = table.get_column_sort_order()

            assert actual_column_sort_order == column_sort_order, (
                'Unexpected column sort order {} != {}'.format(
                    actual_column_sort_order, column_sort_order))


@pytest.mark.usefixtures('inventory')
def test_inventories_table_sort(ui_inventories):
    check_table_sort(ui_inventories.table)


@pytest.mark.usefixtures('project')
def test_projects_table_sort(ui_projects):
    check_table_sort(ui_projects.table)


@pytest.mark.usefixtures('job_template')
def test_job_templates_table_sort(ui_job_templates):
    check_table_sort(ui_job_templates.table)


@pytest.mark.usefixtures(
    'authtoken',
    'install_enterprise_license_unlimited',
    'job_with_status_completed'
)
def test_jobs_table_sort(ui_jobs):
    check_table_sort(ui_jobs.jobs.table)


@pytest.mark.usefixtures('anonymous_user')
def test_users_table_sort(ui_users):
    check_table_sort(ui_users.table)


@pytest.mark.usefixtures('team')
def test_teams_table_sort(ui_teams):
    check_table_sort(ui_teams.table)
