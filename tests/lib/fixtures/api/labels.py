import pytest
import fauxfactory


@pytest.fixture(scope="function")
def label(request, authtoken, organization, api_labels_pg):
    payload = dict(name="label - %s" % fauxfactory.gen_utf8(), organization=organization.id)
    return api_labels_pg.post(payload)
