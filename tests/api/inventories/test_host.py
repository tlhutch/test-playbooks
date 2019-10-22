import awxkit.exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestHost(APITest):

    def test_duplicate_hosts_disallowed_in_same_inventory(self, factories):
        host = factories.host()
        with pytest.raises(exc.Duplicate) as e:
            factories.host(name=host.name, inventory=host.ds.inventory)
        assert e.value[1]['__all__'] == ['Host with this Name and Inventory already exists.']

    def test_jinja_in_inventory_hostname_fail(self, factories):
        with pytest.raises(exc.BadRequest) as e:
            factories.host(name="{{ lookup('pipe', 'touch /tmp/foo') }}")
        assert 'Inline Jinja variables are not allowed' in str(e.value)
