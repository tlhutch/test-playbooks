import json
import pytest
import logging
import common.tower.inventory
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Scripts(Base_Api_Test):
    '''
    Verifies basic CRUD operations against the /inventory_scripts endpoint
    '''
    def test_post(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        '''
        Verify POST
        '''
        # if we make it through the fixures, post worked
        assert True

    def test_get(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        '''
        Verify GET
        '''
        inventory_script.get()

    def test_duplicate(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        '''
        Verify POST duplicate
        '''
        with pytest.raises(common.exceptions.Duplicate_Exception):
            api_inventory_scripts_pg.post(inventory_script.json)

    def test_filter(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        '''
        Verify GET
        '''
        # Issue GET against /inventory_scripts/ endpoint
        for attr in ('id', 'name', 'description'):
            filter = {attr: getattr(inventory_script, attr)}
            filter_results = api_inventory_scripts_pg.get(**filter)
            assert filter_results.count == 1, \
                "Filtering by %s returned unexpected number of results (%s != %s)" % \
                (attr, filter_results.count, 1)

    def test_put(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        payload = dict(name=common.utils.random_unicode(),
                       description="Random inventory script - %s" % common.utils.random_unicode(),
                       script='#!/bin/bash\necho "%s"\n' % common.utils.random_unicode())
        for key, val in payload.items():
            setattr(inventory_script, key, val)
        inventory_script.put()
        inventory_script.get()
        for key, val in payload.items():
            assert getattr(inventory_script, key) == val, \
                "Unexpected value for %s field ('%s' != '%s')" % \
                (key, getattr(inventory_script, key), val)

    def test_patch(self, ansible_runner, api_inventory_scripts_pg, inventory_script):
        payload = dict(name=common.utils.random_unicode(),
                       description="Random inventory script - %s" % common.utils.random_unicode(),
                       script='#!/bin/bash\necho "%s"\n' % common.utils.random_unicode())
        inventory_script.patch(**payload)
        inventory_script.get()
        for key, val in payload.items():
            assert getattr(inventory_script, key) == val, \
                "Unexpected value for %s field ('%s' != '%s')" % \
                (key, getattr(inventory_script, key), val)

    def test_delete(self, ansible_runner, tower_version_cmp, api_inventory_scripts_pg, inventory_script):
        '''
        Verify POSTing an inventory script
        '''

        # delete script
        inventory_script.delete()

        # attempt to GET script
        with pytest.raises(common.exceptions.NotFound_Exception):
            inventory_script.get()

        # query /inventory_sources endpoint for matching id
        assert api_inventory_scripts_pg.get(id=inventory_script.id).count == 0
