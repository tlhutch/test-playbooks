"""Configuration for pytest plugins and fixtures"""
import os
import sys
import pkgutil

# Add tests/lib directory to path
conftest_dir = os.path.dirname(__file__)
lib_dir = os.path.join(conftest_dir, 'lib')
if os.path.isdir(lib_dir):
    sys.path.insert(0, lib_dir)

import plugins  # NOQA
import plugins.pytest_restqa  # NOQA
import markers  # NOQA
import fixtures  # NOQA
import fixtures.api  # NOQA


# Load any plugins, fixtures and markers
def _pytest_plugins_generator(*extension_pkgs):
    # Finds all submodules in pytest extension packages and loads them
    found_plugins = set()
    for extension_pkg in extension_pkgs:
        path = extension_pkg.__path__
        prefix = f'{extension_pkg.__name__}.'
        for importer, modname, is_package in pkgutil.iter_modules(path, prefix):
            if not is_package:
                found_plugins.add(modname)
    return list(found_plugins)


# Automatically import plugins
pytest_plugins = _pytest_plugins_generator(fixtures, markers, plugins, fixtures.api)
# Manually add other plugins
pytest_plugins += [
    plugins.pytest_restqa.plugin.__name__,
    fixtures.api.__name__,
]


def pytest_addoption(parser):
    parser.addoption('--base-url',
                     action='store',
                     dest='base_url',
                     help='base url of tower instance under test')
