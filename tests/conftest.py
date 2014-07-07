'''conftest.py

1) Update sys.path to include 'tests/lib'
2) Automatically import a number of pytest plugins and fixtures
'''

import os
import sys
import pkgutil
import pytest
import inspect

# Add tests/lib directory to path
conftest_dir = os.path.dirname(__file__)
lib_dir = os.path.join(conftest_dir, 'lib')
if os.path.isdir(lib_dir):
    sys.path.insert(0, lib_dir)

import plugins
import plugins.pytest_restqa
import fixtures
import markers

# Load any plugins, fixtures and markers
def _pytest_plugins_generator(*extension_pkgs):
    # Finds all submodules in pytest extension packages and loads them
    for extension_pkg in extension_pkgs:
        path = extension_pkg.__path__
        prefix = '%s.' % extension_pkg.__name__
        for importer, modname, is_package in pkgutil.iter_modules(path, prefix):
            if not is_package:
                yield modname

pytest_plugins = tuple(_pytest_plugins_generator(fixtures, markers, plugins))

# Include plugins/pytest_restqa
pytest_plugins += (plugins.pytest_restqa.pytest_restqa.__name__,)
