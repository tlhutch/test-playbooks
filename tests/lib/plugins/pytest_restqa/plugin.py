import httplib
import logging
import sys

import requests
import pytest
import py

from towerkit.utils import load_credentials
from towerkit.api.client import Connection
from towerkit import config as qe_config


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

    group = parser.getgroup('safety', 'safety')
    group.addoption('--api-destructive',
                    action='store_true',
                    dest='run_destructive',
                    default=False,
                    help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')

    group = parser.getgroup('credentials', 'credentials')
    group.addoption('--api-credentials',
                    action='store',
                    dest='credentials_file',
                    metavar='path',
                    help='location of yaml file containing user credentials.')


connections = {}


def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):
        config.addinivalue_line(
            'markers', 'nondestructive: mark the test as nondestructive. '
            'Tests are assumed to be destructive unless this marker is '
            'present. This reduces the risk of running destructive '
            'tests accidentally.')

        if not config.option.run_destructive:
            if config.option.markexpr:
                config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
            else:
                config.option.markexpr = 'nondestructive'

    # If --debug was provided, set the root logger to logging.DEBUG
    if config.option.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    if config.option.debug_rest:
        config._debug_rest_hdlr = logging.FileHandler('pytestdebug-rest.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        config._debug_rest_hdlr.setFormatter(formatter)

    if not (config.option.help or config.option.collectonly or config.option.showfixtures or config.option.markers):
        if config.option.base_url:
            try:
                r = requests.get(config.option.base_url, verify=False, timeout=5)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError), e:
                errstr = "Unable to connect to %s, %s" % (config.option.base_url, e)
                py.test.fail(msg=errstr)
                # I'm unclear why the following does not emit the error to stdout
                # py.test.exit(errstr)

            assert r.status_code == httplib.OK, \
                "Base URL did not return status code %s. (URL: %s, Response: %s)" % \
                (httplib.OK, config.option.base_url, r.status_code)

            qe_config.base_url = config.option.base_url

            # Load credentials.yaml
            if config.option.credentials_file:
                qe_config.credentials = load_credentials(config.option.credentials_file)

            qe_config.assume_untrusted = config.getvalue('assume_untrusted')

            connections['root'] = Connection(qe_config.base_url, verify=not qe_config.assume_untrusted)

            if config.option.debug_rest and hasattr(config, '_debug_rest_hdlr'):
                logger = logging.getLogger('towerkit.api.client')
                logger.setLevel('DEBUG')
                logger.addHandler(config._debug_rest_hdlr)


@pytest.fixture(scope='session')
def connection():
    return connections['root']


@pytest.mark.trylast
def pytest_unconfigure(config):
    # Print reminder about pytestdebug-rest.log
    if hasattr(config, '_debug_rest_hdlr'):
        sys.stderr.write("Wrote pytest-rest information to %s\n" % config._debug_rest_hdlr.baseFilename)


@pytest.mark.hookwrapper
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
