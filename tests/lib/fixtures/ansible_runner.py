import pytest


@pytest.fixture(scope='class')
def ansible_runner(ansible_module_cls):
    return ansible_module_cls
