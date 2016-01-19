import pytest

from tests.ui import BaseTestUI


@pytest.mark.login
class TestDashboard(BaseTestUI):

    def test_page_layout(self, ui_dashboard):
        """Verify page component visibility as a superuser
        """
        assert ui_dashboard.graphs.is_displayed(), (
            'Unable to locate dashboard graphs')

        assert ui_dashboard.job_status_graph_tab.is_displayed(), (
            'Unable to locate dashboard job status graph tab')

        assert ui_dashboard.host_status_graph_tab.is_displayed(), (
            'Unable to locate dashboard host status graph tab')

        ui_dashboard.host_status_graph_tab.click()

        assert ui_dashboard.host_status_graph.is_displayed(), (
            'Unable to locate host status graph')

        ui_dashboard.job_status_graph_tab.click()

        assert ui_dashboard.job_status_graph.is_displayed(), (
            'Unable to locate job status graph')

        assert ui_dashboard.job_templates_list.is_displayed(), (
            'Unable to locate job templates list')

        assert ui_dashboard.jobs_list.is_displayed(), (
            'Unable to locate job slist')
