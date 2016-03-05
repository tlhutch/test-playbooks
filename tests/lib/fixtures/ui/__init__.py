import pytest


@pytest.fixture
def default_credentials(mozwebqa):
    plugin = pytest.config.pluginmanager.getplugin('pytest_mozwebqa')
    return plugin.TestSetup.credentials['default']
