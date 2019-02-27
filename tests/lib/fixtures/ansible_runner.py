import pytest


@pytest.fixture
def ansible_runner(ansible_module):
    return ansible_module
