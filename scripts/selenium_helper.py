import argparse
import pytest_mozwebqa.credentials
import pytest_mozwebqa.selenium_client
from towerkit.ui.pages import Login_Page
from selenium.webdriver.common.by import By  # NOQA
from IPython.frontend.terminal.embed import InteractiveShellEmbed


class TestSetup(object):
    '''Mock mozwebqa class'''
    def __init__(self, args):
        self.base_url = args.base_url
        self.credentials = pytest_mozwebqa.credentials.read('tests/credentials.yml')

        args.sauce_labs_credentials_file = None
        args.host = 'localhost'
        args.port = 4444
        args.api = 'WEBDRIVER'
        args.assume_untrusted = True
        args.capture_network = False
        args.proxy_host = None
        args.proxy_port = None
        args.browser = None

        args.capabilities = None
        args.chrome_path = None
        args.chrome_options = None
        args.firefox_path = None
        args.firefox_preferences = None
        args.profile_path = None
        args.extension_paths = []
        args.opera_path = None
        args.timeout = 60
        args.webqatimeout = 60

    @property
    def selenium(self):
        return self.selenium_client.selenium

    @property
    def timeout(self):
        return self.selenium_client.timeout

    @property
    def default_implicit_wait(self):
        return self.selenium_client.default_implicit_wait

    def start(self):
        self.selenium_client = pytest_mozwebqa.selenium_client.Client('manual', args)
        self.selenium_client.start()

    def stop(self):
        self.selenium_client.stop()


def parse_args():
    parser = argparse.ArgumentParser(description='Manually test selenium selectors.')
    parser.add_argument('--nologin', action='store_true',
                        default=False,
                        help="Don't login on startup")
    parser.add_argument('--url', dest='base_url', action='store',
                        default=None, required=True,
                        help='Specify URL')
    parser.add_argument('--driver', dest='driver', action='store',
                        default='firefox', required=True,
                        choices=['firefox', 'chrome', 'safari'],
                        help='Specify selenium driver (default: %(default)s)')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    # Setup mozwebqa UI helper
    mozwebqa = TestSetup(args)
    mozwebqa.start()

    # login
    login_pg = Login_Page(mozwebqa).go_to_login_page()
    if not args.nologin:
        home_pg = login_pg.login()

    # Start interactive ipython shell
    shell = InteractiveShellEmbed(banner2='*** Selenium Shell ***')
    shell()

    # Stop mozwebqa
    mozwebqa.stop()
