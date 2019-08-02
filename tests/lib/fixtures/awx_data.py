import pytest
from awxkit.yaml_file import load_file


def pytest_addoption(parser):
    group = parser.getgroup('awx', 'awx')
    group._addoption('--awx-data-file', action='store', default=None,  # default='testdata.yaml',
                     dest='awx_data_filename', metavar='AWX_DATA',
                     help='location of yaml file containing fixture data (default: %default)')


def pytest_runtest_setup(item):
    """If awx_data_filename is None, it will be autoloaded"""
    if item.config.getvalue('awx_data_filename'):
        AwxConfig.data = load_file(item.config.option.awx_data_filename)


@pytest.fixture(scope="module")
def awx_data(request):
    return AwxConfig(request)


class AwxConfig():
    """This class is just used for monkey patching"""

    def __init__(self, request):
        self.request = request

        # If empty, load the global yaml config
        if hasattr(self, 'data') and not self.data:
            self.data = load_file(request.config.getvalue('awx_data_filename'))

    def __getitem__(self, key):
        return self.data.__getitem__(key)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)
