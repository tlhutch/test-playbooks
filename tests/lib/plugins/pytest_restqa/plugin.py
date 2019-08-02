import http.client
import logging
import os
import sys

import requests
import pytest

from awxkit.tower.utils import uses_sessions
from awxkit.utils import load_credentials
from awxkit.utils import PseudoNamespace
from awxkit.api.client import Connection
from awxkit import config as qe_config
from awxkit import yaml_file


__version__ = '1.0'


log = logging.getLogger(__name__)


def pytest_addoption(parser):
    group = parser.getgroup('rest', 'rest')
    group.addoption('--api-untrusted',
                    action='store_true',
                    dest='assume_untrusted',
                    default=False,
                    help='assume that all certificate issuers are untrusted. (default: %default)')
    # FIXME - make this work (refer to lib/common/api.py)
    group.addoption('--api-debug',
                    action='store_true',
                    dest='debug_rest',
                    default=False,
                    help='record REST API calls in pytestdebug-rest.log.')

    group = parser.getgroup('credentials', 'credentials')
    group.addoption('--api-credentials',
                    action='store',
                    dest='credentials_file',
                    metavar='path',
                    help='location of yaml file containing user credentials.')

    group = parser.getgroup('resource-loading', 'resource-loading')
    group.addoption('--resource-file',
                    action='store',
                    dest='resource_file',
                    metavar='path',
                    help='YAML file that specifies resources expected on the Tower instance.')

    group = parser.getgroup('openshift-namespace', 'openshift-namespace')
    group.addoption('--openshift-namespace',
                    action='store',
                    dest='openshift_namespace',
                    default=os.getenv('OPENSHIFT_PROJECT', 'tower-qe'),
                    help='OpenShift namespace to run test against')


connections = {}


def set_connection(base_url, config):
    """Attempt to establish a connection with the given tower base url."""
    try:
        r = requests.get(base_url, verify=False, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        errstr = "Unable to connect to %s, %s" % (config.option.base_url, e)
        pytest.fail(msg=errstr)
        # I'm unclear why the following does not emit the error to stdout
        # py.test.exit(errstr)

    assert r.status_code == http.client.OK, \
        "Base URL did not return status code %s. (URL: %s, Response: %s)" % \
        (http.client.OK, base_url, r.status_code)

    qe_config.base_url = base_url

    # Load credentials.yaml
    if config.option.credentials_file:
        qe_config.credentials = load_credentials(config.option.credentials_file)

    qe_config.assume_untrusted = config.getvalue('assume_untrusted')

    # Making requests with the shared connection is destructive to multiprocessed page fixtures
    # for an undetermined reason. All pre-run env checks must be done with separate requests session.
    env_connection = Connection(qe_config.base_url, verify=not qe_config.assume_untrusted)
    qe_config.use_sessions = uses_sessions(env_connection)

    connections['root'] = Connection(qe_config.base_url, verify=not qe_config.assume_untrusted)


def pytest_configure(config):
    # If --debug was provided, set the root logger to logging.DEBUG
    if config.option.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    if config.option.debug_rest:
        config._debug_rest_hdlr = logging.FileHandler('pytestdebug-rest.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        config._debug_rest_hdlr.setFormatter(formatter)

    if config.option.resource_file:
        qe_config.resources = PseudoNamespace(yaml_file.load_file(config.option.resource_file))

    if not (config.option.help or config.option.collectonly or config.option.showfixtures or config.option.markers):
        if config.option.base_url:
            set_connection(config.option.base_url, config)
            if config.option.debug_rest and hasattr(config, '_debug_rest_hdlr'):
                for mod in ('awxkit.api.client', 'awxkit.ws'):
                    logger = logging.getLogger(mod)
                    logger.setLevel('DEBUG')
                    logger.addHandler(config._debug_rest_hdlr)

    qe_config.openshift_namespace = config.option.openshift_namespace


@pytest.fixture(scope='session')
def connection():
    """
    Note that because of scoping, return value is effectively cached for duration of test run.
    Even setting scope to `function` here would not give a means of retrieving the connection that
    had been changed _within a test_. In order to get the current connection, see `current_connection`
    fixture.
    """
    if connections.get('root'):
        return connections['root']
    else:
        pytest.fail('No root connection found, try providing a --base-url to the pytest invocation')


@pytest.fixture(scope='session')
def current_connection():
    """returns callable that gives current connection"""
    return lambda: connections['root']


@pytest.mark.trylast
def pytest_unconfigure(config):
    # Print reminder about pytestdebug-rest.log
    if hasattr(config, '_debug_rest_hdlr'):
        sys.stderr.write("Wrote pytest-rest information to %s\n" % config._debug_rest_hdlr.baseFilename)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    if 'skip_restqa' in item.keywords:
        return

    if call.when == 'setup':
        if hasattr(item.config, '_debug_rest_hdlr'):
            # log rest info
            msg = '==== {0} ====\n'
            item.config._debug_rest_hdlr.stream.write(msg.format(item.nodeid))

    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, 'extra', [])
    xfail = hasattr(report, 'wasxfail')

    if report.when == 'call':
        if (report.skipped and xfail) or (report.failed and not xfail):
            if hasattr(item, 'debug'):
                extra.append(('pytest-restqa', _debug_summary(item.debug)))
            report.extra = extra
        else:
            # if the test passed, don't display logs on the html report
            report.sections = []


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)
