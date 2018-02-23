import pytest


@pytest.fixture(scope='class')
def tower_instance_group(v2_class):
    return v2_class.instance_groups.get(name='tower').results.pop()
