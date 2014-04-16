import pytest

@pytest.mark.skip_restqa
@pytest.mark.selenium
class Base_UI_Test(object):
    '''
    Base class
    '''
    @classmethod
    def setup_class(self):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        plugin = pytest.config.pluginmanager.getplugin("mozwebqa")
        assert plugin, 'Unable to find mozwebqa plugin'
        self.testsetup = plugin.TestSetup

    @classmethod
    def teardown_class(self):
        '''
        Perform any required test teardown
        '''

    @property
    def credentials(self):
        '''convenient access to credentials'''
        return self.testsetup.credentials

    def has_credentials(self, ctype, sub_ctype=None, fields=[]):
        '''
        assert whether requested credentials are present
        '''

        # Make sure credentials.yaml has ctype we need
        assert ctype in self.testsetup.credentials, \
            "No '%s' credentials defined in credentals.yaml" % ctype
        creds = self.testsetup.credentials[ctype]

        # Ensure requested sub-type is present
        if sub_ctype:
            assert sub_ctype in creds, \
                "No '%s' '%s' credentials defined in credentals.yaml" % \
                (ctype, sub_ctype)
            creds = creds[sub_ctype]

        # Ensure requested fields are present
        if fields:
            assert all([field in creds for field in fields]), \
                "Not all requested credential fields for section '%s' defined credentials.yaml" % \
                ctype

        return True

