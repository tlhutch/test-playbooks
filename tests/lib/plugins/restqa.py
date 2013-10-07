import py
import re
import yaml
import json
import urllib2


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


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_sessionstart(session):
    import requests
    if session.config.option.base_url and not session.config.option.collectonly:
        r = requests.get(session.config.option.base_url, verify=False)
        assert r.status_code == 200, 'Base URL did not return status code 200. (URL: %s, Response: %s)' % (session.config.option.base_url, r.status_code)


def pytest_runtest_setup(item):
    item.debug = {
        'urls': [],
        'screenshots': [],
        'html': [],
        'logs': [],
        'network_traffic': []}
    TestSetup.base_url = item.config.option.base_url
    if item.config.option.credentials_file:
        TestSetup.credentials = load_credentials(item.config.option.credentials_file)

    test_id = '.'.join(split_class_and_test_names(item.nodeid))

    TestSetup.selenium = None

def pytest_runtest_teardown(item):
    if hasattr(TestSetup, 'selenium') and TestSetup.selenium and 'skip_selenium' not in item.keywords:
        TestSetup.selenium_client.stop()


def pytest_funcarg__testsetup(request):
    '''
    Return initialized REST QA TestSetup object
    '''
    return TestSetup(request)


def pytest_addoption(parser):
    group = parser.getgroup('rest', 'rest')
    group._addoption('--baseurl',
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
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')
    group._addoption('--untrusted',
                     action='store_true',
                     dest='assume_untrusted',
                     default=False,
                     help='assume that all certificate issuers are untrusted. (default: %default)')

    group = parser.getgroup('safety', 'safety')
    group._addoption('--destructive',
                     action='store_true',
                     dest='run_destructive',
                     default=False,
                     help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")


def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
