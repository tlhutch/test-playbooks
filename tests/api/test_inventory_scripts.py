import re
import json
import pytest
import common.tower.inventory
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


bad_scripts = [
    '''#!env python
raise Exception("Fail!")
''',
    '''#!env python
import sys
sys.exit(1)
''',
    '''#!env python
import json
print json.dumps({})
''']


# @pytest.mark.script_source('#!env python\nraise Exception("fail!")\n') # traceback
# @pytest.mark.script_source('#!env python\nimport sys\nsys.exit(1)\n')
@pytest.fixture(scope="function", params=enumerate(bad_scripts))
def bad_inventory_script(request, inventory_script):
    inventory_script.script = request.param[1]
    inventory_script.put()
    return inventory_script


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Scripts(Base_Api_Test):
    '''
    Verifies basic CRUD operations against the /inventory_scripts endpoint
    '''
    def test_post(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful POST to /inventory_scripts
        '''
        # if we make it through the fixures, post worked
        assert True

    def test_get(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful GET to /inventory_scripts
        '''
        inventory_script.get()

    def test_duplicate(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify response when POSTing a duplicate to /inventory_scripts
        '''
        with pytest.raises(common.exceptions.Duplicate_Exception):
            api_inventory_scripts_pg.post(inventory_script.json)

    def test_filter(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify filters with the GET resource
        '''
        # Issue GET against /inventory_scripts/ endpoint
        for attr in ('id', 'name', 'description'):
            filter = {attr: getattr(inventory_script, attr)}
            filter_results = api_inventory_scripts_pg.get(**filter)
            assert filter_results.count == 1, \
                "Filtering by %s returned unexpected number of results (%s != %s)" % \
                (attr, filter_results.count, 1)

    def test_put(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify successful PUT to /inventory_scripts/n
        '''
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

    def test_patch(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify successful PATCH to /inventory_scripts/n
        '''
        payload = dict(name=common.utils.random_unicode(),
                       description="Random inventory script - %s" % common.utils.random_unicode(),
                       script='#!/bin/bash\necho "%s"\n' % common.utils.random_unicode())
        inventory_script.patch(**payload)
        inventory_script.get()
        for key, val in payload.items():
            assert getattr(inventory_script, key) == val, \
                "Unexpected value for %s field ('%s' != '%s')" % \
                (key, getattr(inventory_script, key), val)

    def test_delete(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful DELETE to /inventory_scripts/n
        '''

        # delete script
        inventory_script.delete()

        # attempt to GET script
        with pytest.raises(common.exceptions.NotFound_Exception):
            inventory_script.get()

        # query /inventory_sources endpoint for matching id
        assert api_inventory_scripts_pg.get(id=inventory_script.id).count == 0

    def test_import(self, custom_inventory_source, api_unified_jobs_pg, inventory_script):
        '''
        Verify succesful inventory_update using a custom /inventory_script
        '''

        # POST inventory_update
        update_pg = custom_inventory_source.get_related('update')
        result = update_pg.post()

        # assert JSON response
        assert 'inventory_update' in result.json, "Unexpected JSON response when starting an inventory_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # wait for inventory_update to complete
        jobs_pg = api_unified_jobs_pg.get(id=result.json['inventory_update'])
        assert jobs_pg.count == 1, "Unexpected number of inventory_updates found (%s != 1)" % jobs_pg.count
        job_pg = jobs_pg.results[0].wait_until_completed()

        # assert successful inventory_update
        assert job_pg.is_successful, "Inventory update unsuccessful - %s " % job_pg

        # assert imported groups
        inv_pg = custom_inventory_source.get_related('inventory')
        num_groups = inv_pg.get_related('groups', description='imported').count
        assert num_groups > 0, "Unexpected number of groups (%s) created as a result of an inventory_update" % num_groups

        # assert imported hosts
        num_hosts = inv_pg.get_related('hosts', description='imported').count
        assert num_hosts > 0, "Unexpected number of hosts were imported as a result of an inventory_update" % num_hosts

        # assert expected environment variables
        print json.dumps(job_pg.job_env, indent=2)
        source_vars = json.loads(custom_inventory_source.source_vars)
        for key, val in source_vars.items():
            assert key in job_pg.job_env, "inventory_update.job_env missing expected environment variable '%s'" % key
            if re.match(r'^[A-Z_]', key):
                # assert existing shell environment variables are *not* replaced
                assert job_pg.job_env[key] != val, "The reserved environment variable '%s' was incorrectly set ('%s' != '%s')" % \
                    (key, job_pg.job_env[key], val)
            else:
                # assert new variables are set
                assert job_pg.job_env[key] == val, "The environment variable '%s' was incorrectly set ('%s' != '%s')" % \
                    (key, job_pg.job_env[key], val)

    # @pytest.mark.script_source('#!env python\nraise Exception("fail!")\n') # traceback
    # @pytest.mark.script_source('#!env python\nimport sys\nsys.exit(1)\n')
    def test_import_failure(self, custom_inventory_source, api_unified_jobs_pg, bad_inventory_script):
        '''
        Verify an inventory_update fails when using various bad inventory_scripts
        '''

        # PATCH inventory_source
        custom_inventory_source.patch(source_script=bad_inventory_script.id)

        # POST inventory_update
        update_pg = custom_inventory_source.get_related('update')
        result = update_pg.post()

        # assert JSON response
        assert 'inventory_update' in result.json, "Unexpected JSON response when starting an inventory_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # wait for inventory_update to complete
        jobs_pg = api_unified_jobs_pg.get(id=result.json['inventory_update'])
        assert jobs_pg.count == 1, "Unexpected number of inventory_updates found (%s != 1)" % jobs_pg.count
        job_pg = jobs_pg.results[0].wait_until_completed()

        # assert failed inventory_update
        assert not job_pg.is_successful, "Inventory update completed successfully, but was expected to fail  - %s " % job_pg
