import os
import sys
import re
import yaml
import json
import requests
import httplib
import py
import pytest
import logging
from rest_client import Connection


__version__ = '1.0'


def load_credentials(filename=None):
    if filename is None:
        this_file = os.path.abspath(__file__)
        path = py.path.local(this_file).new(basename='credentials.yaml')
    else:
        path = py.path.local(filename)

    if path.check():
        credentials_fh = path.open()
        credentials_dict = yaml.load(credentials_fh)
        return credentials_dict
    else:
        msg = 'Unable to load credentials file at %s' % path
        raise Exception(msg)


def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):

        config.addinivalue_line(
            'markers', 'nondestructive: mark the test as nondestructive. ' \
            'Tests are assumed to be destructive unless this marker is ' \
            'present. This reduces the risk of running destructive tests ' \
            'accidentally.')

        if not config.option.run_destructive:
            if config.option.markexpr:
                config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
            else:
                config.option.markexpr = 'nondestructive'

    if config.option.debug_rest:
        config._debug_rest_hdlr = logging.FileHandler('pytestdebug-rest.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        config._debug_rest_hdlr.setFormatter(formatter)


@pytest.mark.trylast
def pytest_unconfigure(config):
    # Print reminder about pytestdebug-rest.log
    if hasattr(config, '_debug_rest_hdlr'):
        sys.stderr.write("Wrote pytest-rest information to %s\n" %
            config._debug_rest_hdlr.baseFilename)


def pytest_sessionstart(session):
    '''
    Determine if provided base_url is available
    '''
    if session.config.option.base_url and not session.config.option.collectonly:
        try:
            r = requests.get(session.config.option.base_url, verify=False, timeout=5)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError), e:
            py.test.exit("Unable to connect to %s" % (session.config.option.base_url,))

        assert r.status_code == httplib.OK, \
            "Base URL did not return status code %s. (URL: %s, Response: %s)" % \
            (httplib.OK, session.config.option.base_url, r.status_code)

        TestSetup.base_url = session.config.option.base_url

        # Load credentials.yaml
        if session.config.option.credentials_file:
            TestSetup.credentials = load_credentials(session.config.option.credentials_file)

        TestSetup.api = Connection(session.config.getvalue('base_url'),
            version=session.config.getvalue('api_version'),
            verify=not session.config.getvalue('assume_untrusted'))
        if session.config.option.debug_rest and hasattr(session.config, '_debug_rest_hdlr'):
            TestSetup.api.setup_logging(session.config._debug_rest_hdlr)

def pytest_runtest_setup(item):
    '''
    Per-test setup
    '''
    # NOTE: the following is commented out to speed up tests.  Instead,
    # TestSetup is prepared on a per-session basis (see pytest_sessionstart)

    # TestSetup.base_url = item.config.option.base_url

    # Load credentials.yaml
    # if item.config.option.credentials_file:
    #     TestSetup.credentials = load_credentials(item.config.option.credentials_file)

    # Initialize API Connection
    #TestSetup.api = Connection(TestSetup.base_url,
    #    version=item.config.getvalue('api_version'),
    #    verify=not item.config.getvalue('assume_untrusted'))
    #if item.config.option.debug_rest:
    #    TestSetup.api.setup_logging(item.config._debug_rest_hdlr)


def pytest_runtest_teardown(item):
    '''
    Per-test cleanup
    '''

@pytest.fixture(scope="session")
def testsetup(request):
    '''
    Return initialized REST QA TestSetup object
    '''
    return TestSetup(request)


def pytest_addoption(parser):
    group = parser.getgroup('rest', 'rest')
    group._addoption('--api-baseurl',
        action='store',
        dest='base_url',
        default=None,
        metavar='url',
        help='base url for the application under test.')
    group._addoption('--api-version',
        action='store',
        dest='api_version',
        default='current_version',
        metavar='API-VERSION',
        help='Choose the API version')
    group._addoption('--api-untrusted',
        action='store_true',
        dest='assume_untrusted',
        default=False,
        help='assume that all certificate issuers are untrusted. (default: %default)')
    # FIXME - make this work (refer to lib/common/api.py)
    group.addoption('--api-debug',
        action="store_true",
        dest="debug_rest",
        default=False,
        help="record REST API calls 'pytestdebug-rest.log'.")

    group = parser.getgroup('safety', 'safety')
    group._addoption('--api-destructive',
        action='store_true',
        dest='run_destructive',
        default=False,
        help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--api-credentials",
        action="store",
        dest='credentials_file',
        metavar='path',
        help="location of yaml file containing user credentials.")


def pytest_runtest_makereport(item, call):
    '''
    TODO - figure out how to write to pytestdebug-rest.log
    '''
    if call.when == 'setup':
        if hasattr(TestSetup, 'api') and TestSetup.api and hasattr(item.config, '_debug_rest_hdlr'):
            '''
            log rest info
            '''
            item.config._debug_rest_hdlr.stream.write('==== %s ====\n' % item.nodeid)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
