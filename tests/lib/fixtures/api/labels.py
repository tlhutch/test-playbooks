import pytest


@pytest.fixture(scope="function")
def label(organization, factories):
    label = factories.label(organization=organization)
    return label
