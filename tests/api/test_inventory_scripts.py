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


# @pytest.mark.fixture_args(script_source='#!env python\nraise Exception("fail!")\n') # traceback
# @pytest.mark.fixture_args(script_source='#!env python\nimport sys\nsys.exit(1)\n')
@pytest.fixture(scope="function", params=enumerate(bad_scripts))
def bad_inventory_script(request, inventory_script):
    inventory_script.script = request.param[1]
    inventory_script.put()
    return inventory_script


@pytest.fixture(scope="function")
def custom_inventory_source_vars_good(request):
    return dict(my_custom_boolean=True,
                my_custom_integer=1,
                my_custom_string="STRING")


@pytest.fixture(scope="function")
def custom_inventory_source_vars_bad(request):
    return dict(HOME='BOGUS',
                PATH='BOGUS',
                USER='BOGUS',
                TERM='BOGUS',)


@pytest.fixture(scope="function")
def custom_inventory_source_with_vars(request, custom_inventory_source, custom_inventory_source_vars_good, custom_inventory_source_vars_bad):
    custom_inventory_source.patch(source_vars=json.dumps(dict(custom_inventory_source_vars_good.items() + custom_inventory_source_vars_bad.items())))
    return custom_inventory_source


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Inventory_Scripts(Base_Api_Test):
    '''
    Verifies basic CRUD operations against the /inventory_scripts endpoint
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_post(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful POST to /inventory_scripts
        '''
        # if we make it through the fixures, post worked
        assert True

    def test_post_without_required_fields(self, api_inventory_scripts_pg, organization, script_source):
        '''
        Verify succesful POST to /inventory_scripts
        '''
        # without name
        payload = dict(script=script_source,
                       organization=organization.id)
        with pytest.raises(common.exceptions.BadRequest_Exception):
            api_inventory_scripts_pg.post(payload)

        # without script
        payload = dict(name=common.utils.random_unicode(),
                       organization=organization.id)
        with pytest.raises(common.exceptions.BadRequest_Exception):
            api_inventory_scripts_pg.post(payload)

        # without script that includes hashbang
        payload = dict(name=common.utils.random_unicode(),
                       organization=organization.id,
                       script='import json\nprint json.dumps({})')
        with pytest.raises(common.exceptions.BadRequest_Exception):
            api_inventory_scripts_pg.post(payload)

        # without organization
        payload = dict(name=common.utils.random_unicode(),
                       script=script_source)
        with pytest.raises(common.exceptions.BadRequest_Exception):
            api_inventory_scripts_pg.post(payload)

    def test_post_as_non_superusers(self, non_superusers, user_password, api_inventory_scripts_pg, organization, script_source):
        '''
        Verify POST as an organization user is forbidden.
        '''
        payload = dict(name=common.utils.random_unicode(),
                       description="Random inventory script - %s" % common.utils.random_unicode(),
                       organization=organization.id,
                       script=script_source)

        for org_user in non_superusers:
            with self.current_user(org_user.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    api_inventory_scripts_pg.post(payload)

    def test_get_as_superuser(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful GET to /inventory_scripts
        '''
        inventory_script.get()

    def test_get_as_org_users(self, org_users, user_password, inventory_script):
        '''
        Verify that organization user accounts are able to access the
        the inventory_script, but unable to read the contents.
        '''
        for org_user in org_users:
            with self.current_user(org_user.username, user_password):
                inventory_script = inventory_script.get()
                assert inventory_script.script is None, "An organization user is " \
                    "able to read the 'script' attribute of an inventory_script " \
                    "(%s)" % inventory_script.script

    def test_get_as_anonymous_user(self, anonymous_user, user_password, inventory_script):
        '''
        Verify that an anonymous user is forbidden from seeing
        inventory_scripts associated with an organization.
        '''
        with self.current_user(anonymous_user.username, user_password):
            with pytest.raises(common.exceptions.Forbidden_Exception):
                inventory_script = inventory_script.get()

    def test_duplicate(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify response when POSTing a duplicate to /inventory_scripts
        '''
        # assert duplicate error
        with pytest.raises(common.exceptions.Duplicate_Exception):
            api_inventory_scripts_pg.post(inventory_script.json)

    def test_unique(self, request, api_inventory_scripts_pg, inventory_script, another_organization):
        '''
        Verify response when POSTing a duplicate to /inventory_scripts
        '''
        print json.dumps(inventory_script.json, indent=2)
        payload = dict(name=inventory_script.name,
                       description=inventory_script.description,
                       organization=another_organization.id)

        payload = inventory_script.json
        payload['organization'] = another_organization.id
        print json.dumps(payload, indent=2)

        # assert successful POST
        obj = api_inventory_scripts_pg.post(payload)
        request.addfinalizer(obj.silent_delete)

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

    def test_delete_as_superuser(self, api_inventory_scripts_pg, inventory_script):
        '''
        Verify succesful DELETE to /inventory_scripts/n as a superuser.
        '''

        # delete script
        inventory_script.delete()

        # attempt to GET script
        with pytest.raises(common.exceptions.NotFound_Exception):
            inventory_script.get()

        # query /inventory_sources endpoint for matching id
        assert api_inventory_scripts_pg.get(id=inventory_script.id).count == 0

    def test_delete_as_non_superuser(self, non_superusers, user_password, inventory_script):
        '''
        Verify unsuccesful DELETE to /inventory_scripts/n as an organizational user.
        '''

        for org_user in non_superusers:
            with self.current_user(org_user.username, user_password):
                with pytest.raises(common.exceptions.Forbidden_Exception):
                    inventory_script.delete()

    def test_inventory_update_after_delete(self, custom_inventory_source_with_vars, inventory_script):
        '''
        Verify attempting to run an inventory_update, after deleting the
        associated custom_inventory_script, fails.
        '''

        # grab update_pg page before deleting inventory_script
        update_pg = custom_inventory_source_with_vars.get_related('update')
        assert update_pg.can_update

        # delete the inventory_script
        inventory_script.delete()

        # POST inventory_update
        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            update_pg.post()

        # reload the update_pg
        update_pg.get()
        assert not update_pg.can_update

        # reload the inventory_source
        custom_inventory_source_with_vars.get()
        assert custom_inventory_source_with_vars.source_script is None, \
            "After deleting the inventory_script, the source_script " \
            "attribute still has a value (%s != None)" % \
            custom_inventory_source_with_vars.source_script

    def test_import(self, custom_inventory_source_with_vars, api_unified_jobs_pg, inventory_script,
                    custom_inventory_source_vars_good, custom_inventory_source_vars_bad):
        '''
        Verify succesful inventory_update using a custom /inventory_script
        '''

        # POST inventory_update
        update_pg = custom_inventory_source_with_vars.get_related('update')
        result = update_pg.post()

        # assert JSON response
        assert 'inventory_update' in result.json, "Unexpected JSON response when starting an inventory_update.\n%s" % \
            json.dumps(result.json, indent=2)

        # wait for inventory_update to complete
        jobs_pg = api_unified_jobs_pg.get(id=result.json['inventory_update'])
        assert jobs_pg.count == 1, "Unexpected number of inventory_updates found (%s != 1)" % jobs_pg.count
        job_pg = jobs_pg.results[0].wait_until_completed()

        # assert successful inventory_update
        assert job_pg.is_successful, "Inventory update unsuccessful - %s" % job_pg

        # assert imported groups
        inv_pg = custom_inventory_source_with_vars.get_related('inventory')
        num_groups = inv_pg.get_related('groups', description='imported').count
        assert num_groups > 0, "Unexpected number of groups (%s) created as a result of an inventory_update" % num_groups

        # assert imported hosts
        num_hosts = inv_pg.get_related('hosts', description='imported').count
        assert num_hosts > 0, "Unexpected number of hosts were imported as a result of an inventory_update" % num_hosts

        # assert expected environment variables
        print json.dumps(job_pg.job_env, indent=2)

        # assert existing shell environment variables are *not* replaced
        for key, val in custom_inventory_source_vars_bad.items():
            if key in job_pg.job_env:
                # assert existing shell environment variables are *not* replaced
                assert job_pg.job_env[key] != val, "The reserved environment " \
                    "variable '%s' was incorrectly set ('%s')" % \
                    (key, job_pg.job_env[key])

        # assert environment variables are replaced
        for key, val in custom_inventory_source_vars_good.items():
            # assert the variable has been set
            assert key in job_pg.job_env, "inventory_update.job_env missing " \
                "expected environment variable '%s'" % key
            # assert correct variable value
            assert job_pg.job_env[key] == str(val), "The environment " \
                "variable '%s' was incorrectly set ('%s' != '%s')" % \
                (key, job_pg.job_env[key], val)

    # @pytest.mark.fixture_args(script_source='#!env python\nraise Exception("fail!")\n') # traceback
    # @pytest.mark.fixture_args(script_source='#!env python\nimport sys\nsys.exit(1)\n')
    def test_import_script_failure(self, custom_inventory_source, api_unified_jobs_pg, bad_inventory_script):
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
