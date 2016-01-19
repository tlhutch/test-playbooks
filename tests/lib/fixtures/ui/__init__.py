import pytest

from common.ui.pages import *  # NOQA


@pytest.fixture
def default_credentials(mozwebqa):
    plugin = pytest.config.pluginmanager.getplugin('pytest_mozwebqa')
    return plugin.TestSetup.credentials['default']


@pytest.fixture
def ui_login(mozwebqa):
    return Login(mozwebqa.base_url, mozwebqa.selenium).open()


@pytest.fixture
def ui_dashboard(mozwebqa, default_credentials):
    return Dashboard(mozwebqa.base_url, mozwebqa.selenium, **default_credentials).open()
