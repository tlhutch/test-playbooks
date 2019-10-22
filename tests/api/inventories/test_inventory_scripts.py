import json

import awxkit.exceptions as exc
import fauxfactory
import pytest

from tests.api import APITest


bad_scripts = [
    """#!env python
raise Exception("Fail!")
""",
    """#!env python
import sys
sys.exit(1)
""",
    """#!env python
import json
print(json.dumps({}))
""",
"""#!/bin/sh
cat << EOF
{
  "all": {
    "hosts": [
      "{{ lookup('pipe', 'touch /tmp/foobar') }}",
      "localhost"
    ]
  },
  "_meta": {
    "hostvars": {
      "{{ lookup('pipe', 'touch /tmp/foobar') }}": {},
      "localhost": {
        "ansible_connection": "local",
        "ansible_python_interpreter": "{{ ansible_playbook_python }}"
      }
    }
  }
}
EOF
"""
]


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
    return dict(PATH='BOGUS')


@pytest.fixture(scope="function")
def custom_inventory_source_with_vars(request, custom_inventory_source, custom_inventory_source_vars_good, custom_inventory_source_vars_bad):
    custom_inventory_source.patch(source_vars=json.dumps(dict(list(custom_inventory_source_vars_good.items()) + list(custom_inventory_source_vars_bad.items()))))
    return custom_inventory_source


@pytest.mark.usefixtures('authtoken')
class Test_Inventory_Scripts(APITest):
    """Verifies basic CRUD operations against the /inventory_scripts endpoint"""

    def test_post_as_privileged_user(self, request, script_source, organization, api_inventory_scripts_pg, privileged_user, user_password):
        """Verify succesful POST to /inventory_scripts as privileged user."""
        payload = dict(name="random_inventory_script-%s" % fauxfactory.gen_utf8(),
                       description="Random Inventory Script - %s" % fauxfactory.gen_utf8(),
                       organization=organization.id,
                       script=script_source)
        with self.current_user(privileged_user.username, user_password):
            obj = api_inventory_scripts_pg.post(payload)
        request.addfinalizer(obj.silent_delete)

    def test_post_as_unprivileged_user(self, script_source, organization, api_inventory_scripts_pg, unprivileged_user, user_password):
        """Verify unsuccesful POST to /inventory_scripts as unprivileged user."""
        payload = dict(name=fauxfactory.gen_utf8(),
                       description="Random inventory script - %s" % fauxfactory.gen_utf8(),
                       organization=organization.id,
                       script=script_source)
        with self.current_user(unprivileged_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                api_inventory_scripts_pg.post(payload)

    def test_post_without_required_fields(self, api_inventory_scripts_pg, organization, script_source):
        """Verify succesful POST to /inventory_scripts"""
        # without name
        payload = dict(script=script_source,
                       organization=organization.id)
        exc_info = pytest.raises(exc.BadRequest, api_inventory_scripts_pg.post, payload)
        result = exc_info.value[1]
        assert result == {'name': ['This field is required.']}, \
            "Unexpected API response when posting an inventory_script with a missing value for 'name': %s." % json.dumps(result)

        # without script
        payload = dict(name=fauxfactory.gen_utf8(),
                       organization=organization.id)
        exc_info = pytest.raises(exc.BadRequest, api_inventory_scripts_pg.post, payload)
        result = exc_info.value[1]
        assert result == {'script': ['This field is required.']}, \
            "Unexpected API response when posting an inventory_script with a missing value for 'script': %s." % json.dumps(result)

        # without script that includes hashbang
        payload = dict(name=fauxfactory.gen_utf8(),
                       organization=organization.id,
                       script='import json\nprint(json.dumps({}))')
        exc_info = pytest.raises(exc.BadRequest, api_inventory_scripts_pg.post, payload)
        result = exc_info.value[1]
        assert result == {'script': ['Script must begin with a hashbang sequence: i.e.... #!/usr/bin/env python']}, \
            "Unexpected API response when posting an inventory_script with a script that does not begin with a hashbang sequence: %s." % json.dumps(result)

        # without organization
        payload = dict(name=fauxfactory.gen_utf8(),
                       script=script_source)
        exc_info = pytest.raises(exc.BadRequest, api_inventory_scripts_pg.post, payload)
        result = exc_info.value[1]
        assert result == {'organization': ['This field is required.']}, \
            "Unexpected API response when posting an inventory_script with a missing value for 'organization': %s." % json.dumps(result)

    def test_get_as_privileged_user(self, inventory_script, privileged_user, user_password):
        """Verify succesful GET to /inventory_scripts as privileged_user and that
        script contents viewable.
        """
        with self.current_user(privileged_user.username, user_password):
            inventory_script.get()
            assert inventory_script.script, "A privileged user is " \
                "unable to read the 'script' attribute of an inventory_script (%s)." \
                % inventory_script.script

    def test_get_as_org_user(self, inventory_script, org_user, user_password):
        """Verify that organization user accounts are able to access the
        the inventory_script, but unable to read the contents.
        """
        with self.current_user(org_user.username, user_password):
            inventory_script.get()
            assert not inventory_script.script, "An org_user is " \
                "able to read the 'script' attribute of an inventory_script (%s)" \
                % inventory_script.script

    def test_get_as_anonymous_user(self, anonymous_user, user_password, inventory_script):
        """Verify that an anonymous user is forbidden from seeing
        inventory_scripts associated with an organization.
        """
        with self.current_user(anonymous_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                inventory_script.get()

    def test_duplicate_inventory_scripts_disallowed_by_organization(self, factories):
        inv_script = factories.inventory_script()

        with pytest.raises(exc.Duplicate) as e:
            factories.inventory_script(name=inv_script.name, organization=inv_script.ds.organization)
        assert e.value[1]['__all__'] == ['Custom inventory script with this Name and Organization already exists.']

    def test_unique(self, request, api_inventory_scripts_pg, inventory_script, another_organization):
        """Verify response when POSTing a duplicate to /inventory_scripts"""
        print(json.dumps(inventory_script.json, indent=2))
        payload = dict(name=inventory_script.name,
                       description=inventory_script.description,
                       organization=another_organization.id)

        payload = inventory_script.json
        payload['organization'] = another_organization.id
        print(json.dumps(payload, indent=2))

        # assert successful POST
        obj = api_inventory_scripts_pg.post(payload)
        request.addfinalizer(obj.silent_delete)

    def test_filter(self, api_inventory_scripts_pg, inventory_script):
        """Verify filters with the GET resource"""
        # Issue GET against /inventory_scripts/ endpoint
        for attr in ('id', 'name', 'description'):
            filter = {attr: getattr(inventory_script, attr)}
            filter_results = api_inventory_scripts_pg.get(**filter)
            assert filter_results.count == 1, \
                "Filtering by %s returned unexpected number of results (%s != %s)" % \
                (attr, filter_results.count, 1)

    def test_put(self, api_inventory_scripts_pg, inventory_script):
        """Verify successful PUT to /inventory_scripts/n"""
        payload = dict(name=fauxfactory.gen_utf8(),
                       description="Random inventory script - %s" % fauxfactory.gen_utf8(),
                       script='#!/bin/bash\necho "%s"\n' % fauxfactory.gen_utf8())
        for key, val in payload.items():
            setattr(inventory_script, key, val)
        inventory_script.put()
        inventory_script.get()
        for key, val in payload.items():
            assert getattr(inventory_script, key) == val, \
                "Unexpected value for %s field ('%s' != '%s')" % \
                (key, getattr(inventory_script, key), val)

    def test_patch(self, api_inventory_scripts_pg, inventory_script):
        """Verify successful PATCH to /inventory_scripts/n"""
        payload = dict(name=fauxfactory.gen_utf8(),
                       description="Random inventory script - %s" % fauxfactory.gen_utf8(),
                       script='#!/bin/bash\necho "%s"\n' % fauxfactory.gen_utf8())
        inventory_script.patch(**payload)
        inventory_script.get()
        for key, val in payload.items():
            assert getattr(inventory_script, key) == val, \
                "Unexpected value for %s field ('%s' != '%s')" % \
                (key, getattr(inventory_script, key), val)

    def test_delete_as_privileged_user(self, api_inventory_scripts_pg, inventory_script, privileged_user, user_password):
        """Verify succesful DELETE to /inventory_scripts/N as a privileged user."""
        with self.current_user(privileged_user.username, user_password):
            # delete script
            inventory_script.delete()

            # attempt to GET script
            with pytest.raises(exc.NotFound):
                inventory_script.get()

            # query /inventory_sources endpoint for matching id
            assert api_inventory_scripts_pg.get(id=inventory_script.id).count == 0

    def test_delete_as_unprivileged_user(self, inventory_script, unprivileged_user, user_password):
        """Verify unsuccesful DELETE to /inventory_scripts/N as an unprivileged user."""
        with self.current_user(unprivileged_user.username, user_password):
            with pytest.raises(exc.Forbidden):
                inventory_script.delete()

    def test_inventory_update_after_delete(self, custom_inventory_source_with_vars, inventory_script):
        """Verify attempting to run an inventory_update, after deleting the
        associated custom_inventory_script, fails.
        """
        # grab update_pg page before deleting inventory_script
        update_pg = custom_inventory_source_with_vars.get_related('update')
        assert update_pg.can_update

        # delete the inventory_script
        inventory_script.delete()

        # POST inventory_update
        with pytest.raises(exc.MethodNotAllowed):
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

    @pytest.mark.yolo
    @pytest.mark.ansible_integration
    def test_import(self, custom_inventory_source_with_vars, api_unified_jobs_pg, inventory_script,
                    custom_inventory_source_vars_good, custom_inventory_source_vars_bad):
        """Verify succesful inventory_update using a custom /inventory_script"""
        # Update inventory_source and wait for completion
        update_pg = custom_inventory_source_with_vars.update().wait_until_completed()

        # assert successful inventory_update
        update_pg.assert_successful()

        # assert imported groups
        inv_pg = custom_inventory_source_with_vars.get_related('inventory')
        num_groups = inv_pg.get_related('groups', description='imported').count
        assert num_groups > 0, "Unexpected number of groups (%s) created as a result of an inventory_update" % num_groups

        # assert imported hosts
        num_hosts = inv_pg.get_related('hosts', description='imported').count
        assert num_hosts > 0, "Unexpected number of hosts were imported as a result of an inventory_update" % num_hosts

        # assert expected environment variables
        print(json.dumps(update_pg.job_env, indent=2))

        # assert existing shell environment variables are *not* replaced
        for key, val in custom_inventory_source_vars_bad.items():
            assert key in update_pg.job_env
            assert update_pg.job_env[key] != val, "The reserved environment " \
                "variable '%s' was incorrectly set ('%s')" % \
                (key, update_pg.job_env[key])

        # assert environment variables are replaced
        for key, val in custom_inventory_source_vars_good.items():
            # assert the variable has been set
            assert key in update_pg.job_env, "inventory_update.job_env missing " \
                "expected environment variable '%s'" % key
            # assert correct variable value
            assert update_pg.job_env[key] == str(val), "The environment " \
                "variable '%s' was incorrectly set ('%s' != '%s')" % \
                (key, update_pg.job_env[key], val)

    def test_confirm_prohibited_source_vars_rejected(self, custom_inventory_source_with_vars):
        for forbidden in ('TERM', 'USER', 'HOME'):
            with pytest.raises(exc.BadRequest) as e:
                custom_inventory_source_with_vars.patch(source_vars=json.dumps({forbidden: 'should_not_allow'}))
            assert e.value.msg == {'source_vars': ['`{}` is a prohibited environment variable'.format(forbidden)]}

    @pytest.mark.ansible_integration
    def test_import_script_failure(self, factories, api_unified_jobs_pg, bad_inventory_script):
        """Verify an inventory_update fails when using various bad inventory_scripts"""
        # PATCH inventory_source
        org = bad_inventory_script.related.organization.get()
        inventory = factories.inventory(organization=org)
        custom_inventory_source = factories.inventory_source(source_script=bad_inventory_script, inventory=inventory)
        assert custom_inventory_source.source_script == bad_inventory_script.id

        # Update inventory_source and wait for completion
        update_pg = custom_inventory_source.update().wait_until_completed()

        # assert failed inventory_update
        assert not update_pg.is_successful, "update completed successfully, but was expected to fail  - %s " % update_pg
