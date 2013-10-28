import pytest

@pytest.mark.skip_selenium
class Base_Api_Test(object):
    '''
    Base class
    '''
    @classmethod
    def setup_class(self):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        plugin = pytest.config.pluginmanager.getplugin("plugins.pytest_restqa.pytest_restqa")
        assert plugin, 'Unable to find pytest_restqa plugin'
        self.testsetup = plugin.TestSetup

    @classmethod
    def teardown_class(self):
        '''
        Perform any required test teardown
        '''
