import pytest


@pytest.fixture
def ansible_runner(ansible_module):
    return ansible_module

@pytest.fixture(scope='class')
def ansible_runner_class(ansible_module):
    return ansible_module
