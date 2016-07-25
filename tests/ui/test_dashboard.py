import pytest


pytestmark = [
    pytest.mark.ui,
    pytest.mark.nondestructive,
    pytest.mark.usefixtures(
        'authtoken',
        'install_enterprise_license',
        'max_window',
    )
]


# -----------------------------------------------------------------------------
# Assertion Helpers and Utilities
# -----------------------------------------------------------------------------

def check_toolbar_dropdown(dropdown):
    for option in dropdown.options:
        dropdown.set_value(option)
        selected = dropdown.get_value()
        assert selected == option, (
            'unexpected value: {1} != {2}'.format(selected, option))


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_job_status_toolbar_dropdowns(ui_dashboard):
    check_toolbar_dropdown(ui_dashboard.toolbar.period)
    check_toolbar_dropdown(ui_dashboard.toolbar.job_type)
    check_toolbar_dropdown(ui_dashboard.toolbar.status)
