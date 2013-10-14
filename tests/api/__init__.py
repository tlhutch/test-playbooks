import pytest

class Base_Api_Test(object):
    '''
    Base class
    '''
    @classmethod
    def setup_class(self):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        self.testsetup = pytest.config.pluginmanager.getplugin("plugins.restqa").TestSetup

    @classmethod
    def teardown_class(self):
        '''
        Perform any required test teardown
        '''
