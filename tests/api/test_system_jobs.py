import json
import pytest
import common.tower.inventory
import common.exceptions
import re
from tests.api import Base_Api_Test


def convert_to_camelcase(s):
    return ''.join(x.capitalize() or '_' for x in s.split('_'))


@pytest.fixture(scope="function", params=['cleanup_jobs_with_status_completed',
                                          'cleanup_deleted_with_status_completed',
                                          'cleanup_activitystream_with_status_completed',
                                          'cleanup_deleted_with_status_completed',
                                          'custom_inventory_update_with_status_completed',
                                          'project_update_with_status_completed',
                                          'job_with_status_completed',
                                          'ad_hoc_with_status_completed'])
def unified_job_with_status_completed(request):
    '''
    Launches jobs of all types sequentially.

    Returns the job run.
    '''
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def multiple_jobs_with_status_completed(cleanup_jobs_with_status_completed,
                                        cleanup_deleted_with_status_completed,
                                        cleanup_activitystream_with_status_completed,
                                        cleanup_facts_with_status_completed,
                                        custom_inventory_update_with_status_completed,
                                        project_update_with_status_completed,
                                        job_with_status_completed,
                                        ad_hoc_with_status_completed):
    '''
    Launches all four system jobs, an inventory update, an SCM update, a job template, and an ad hoc command.

    Returns a list of the jobs run.
    '''
    return [cleanup_jobs_with_status_completed,
            cleanup_deleted_with_status_completed,
            cleanup_activitystream_with_status_completed,
            cleanup_facts_with_status_completed,
            custom_inventory_update_with_status_completed,
            project_update_with_status_completed,
            job_with_status_completed,
            ad_hoc_with_status_completed]


@pytest.fixture(scope="function", params=['organization', 'org_user', 'team',
                                          'ssh_credential', 'project',
                                          'inventory', 'job_template',
                                          'job_with_status_completed'])
def old_deleted_object(request, ansible_runner, tmpdir):
    '''
    Creates and deletes an object.

    Returns the deleted object.
    '''
    obj = request.getfuncargvalue(request.param)
    obj.delete()

    # The following is no longer required now that we have 'tower-manage age_deleted'
    if False:
        # Create python script to age the deleted object
        py_script = '''#!/usr/bin/env python
import sys
import re

# prepare tower environment
from awx import prepare_env
prepare_env()
from awx.main import models

# parse arguments
if len(sys.argv) == 3:
   obj_type = sys.argv[1]
   obj_id = sys.argv[2]
else:
   print "Usage: %s <object-type> <id>" % sys.argv[0]
   sys.exit(1)

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# Assert tower model exists
assert hasattr(models, obj_type), "No tower model found matching name: %s" % obj_type

# Assert object id
obj_cls = getattr(models, obj_type)
obj = obj_cls.objects.get(id=obj_id)

# Determine id and name attributes
if obj_type == 'User':
    name_attr = 'username'
    active_attr = 'is_active'
else:
    name_attr = 'name'
    active_attr = 'active'

# Assert that the object is inactive
assert not getattr(obj, active_attr), "The object is still marked as active"

# Extract deleted datestamp from the object name
obj_name = getattr(obj, name_attr)
match = re.match(r'^(_\w*_)(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[^_]+)(.*)$', obj_name)
if not match:
    raise Exception("Unable to parse name attribute for a datestamp: %s" % obj_name)

try:
    deleted_date = parse(match.group(2))
except Exception, e:
    raise Exception("Unable to parse date from object name: %s - %s" % (match.group(2), e))

deleted_date = deleted_date - relativedelta(days=365)
print("BEFORE: %s" % obj_name.encode('ascii', 'replace'))
new_name = match.group(1) + deleted_date.strftime('%Y-%m-%dT%H:%M:%S.%f%z') + match.group(3)
setattr(obj, name_attr, new_name)
print("AFTER: %s" % new_name.encode('ascii', 'replace'))
obj.save()
'''
        p = tmpdir.mkdir("ansible").join("age.py")
        fd = p.open('w+')
        fd.write(py_script)
        fd.close()

        # copy script to test system
        contacted = ansible_runner.copy(src=fd.name, dest='/tmp/%s' % p.basename, mode='0755')
        result = contacted.values()[0]
        assert 'failed' not in result, "ansible.copy unexpectedly failed - %s" % json.dumps(result, indent=2)

        # age the deleted object
        contacted = ansible_runner.command("%s %s %s" % (result['dest'], convert_to_camelcase(obj.type), obj.id))
        result = contacted.values()[0]
        assert result['rc'] == 0, "ansible.command unexpectedly failed - %s" % json.dumps(result, indent=2)

    # age the deleted object
    cmd = "tower-manage age_deleted --days 365 --id %s --type %s" % (obj.id, convert_to_camelcase(obj.type))
    contacted = ansible_runner.command(cmd)
    result = contacted.values()[0]
    assert result['rc'] == 0, "tower-manage age_deleted unexpectedly failed - %s" % json.dumps(result, indent=2)
    assert result['stdout'] == "Aged 1 items"

    # return the deleted object
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_System_Jobs(Base_Api_Test):
    '''
    Verify actions with system_job_templates
    '''

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_unlimited')

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_superuser(self, system_job):
        '''
        Verify that a superuser account is able to GET a system_job resource.
        '''
        system_job.get()

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_get_as_non_superuser(self, non_superusers, user_password, api_system_jobs_pg, system_job):
        '''
        Verify that non-superuser accounts are unable to access a system_job.
        '''
        for non_superuser in non_superusers:
            with self.current_user(non_superuser.username, user_password):
                with pytest.raises(common.exceptions.NotFound_Exception):
                    api_system_jobs_pg.get(id=system_job.id)

    @pytest.mark.fixture_args(days=1000, granularity='1y', older_than='1y')
    def test_method_not_allowed(self, system_job):
        '''
        Verify that PUT, POST and PATCH are unsupported request methods
        '''
        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.post()

        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.put()

        with pytest.raises(common.exceptions.Method_Not_Allowed_Exception):
            system_job.patch()

    def test_cleanup_jobs(self, cleanup_jobs_template, unified_job_with_status_completed, api_jobs_pg, api_system_jobs_pg, api_unified_jobs_pg):
        '''
        Run jobs of different types sequentially and check that cleanup jobs deletes all of them.
        '''
        # launch cleanup job
        payload = dict(extra_vars=dict(days=0))
        cleanup_jobs_pg = cleanup_jobs_template.launch(payload).wait_until_completed()

        # check cleanup job status
        assert cleanup_jobs_pg.is_successful, "Job unsuccessful - %s" % cleanup_jobs_pg

        # assert provided job has been deleted
        if unified_job_with_status_completed.type not in ['inventory_update', 'project_update']:
            with pytest.raises(common.exceptions.NotFound_Exception):
                unified_job_with_status_completed.get()

        # query for unified_jobs matching the provided job id
        results = api_unified_jobs_pg.get(id=unified_job_with_status_completed.id)

        # calculate expected count
        if unified_job_with_status_completed.type in ['inventory_update', 'project_update']:
            expected_count = 1
        else:
            expected_count = 0

        # assert no matching jobs found
        assert results.count == expected_count, "An unexpected number of unified jobs were found (%s != %s)" \
            % (results.count, expected_count)

    def test_cleanup_jobs_on_multiple_jobs(self, cleanup_jobs_template, multiple_jobs_with_status_completed, api_jobs_pg, api_system_jobs_pg,
                                           api_unified_jobs_pg):
        '''
        Run jobs of different types and check that cleanup jobs deletes all of them.
        '''
        # pretest
        job_types = [uj.type for uj in multiple_jobs_with_status_completed]

        # assert expected jobs are present
        jobs_pg = api_jobs_pg.get()
        assert jobs_pg.count >= job_types.count('job'), "An unexpected number of jobs were found (%s < %s)" \
            % (jobs_pg.count, job_types.count('job'))

        system_jobs_pg = api_system_jobs_pg.get()
        assert system_jobs_pg.count >= job_types.count('system_job'), "An unexpected number of system jobs were found (%s < %s)" \
            % (system_jobs_pg.count, job_types.count('system_job'))

        unified_jobs_pg = api_unified_jobs_pg.get()
        assert unified_jobs_pg.count >= len(job_types), "An unexpected number of unified jobs were found were found (%s < %s)" \
            % (unified_jobs_pg.count, len(job_types))

        # launch cleanup job
        payload = dict(extra_vars=dict(days=0))
        cleanup_jobs_pg = cleanup_jobs_template.launch(payload).wait_until_completed()

        # check cleanup job status
        assert cleanup_jobs_pg.is_successful, "Job unsuccessful - %s" % cleanup_jobs_pg

        # assert jobs_pg is empty
        jobs_pg = api_jobs_pg.get()
        assert jobs_pg.count == 0, "jobs_pg.count not zero (%s != 0)" % jobs_pg.count

        # assert that the cleanup_jobs job is the only job listed in system jobs
        system_jobs_pg = api_system_jobs_pg.get()
        assert system_jobs_pg.count == 1, "An unexpected number of system_jobs were found after running cleanup_jobs (%s != 1)" % system_jobs_pg.count
        assert system_jobs_pg.results[0].id == cleanup_jobs_pg.id, "After running cleanup_jobs, an unexpected system_job.id was found (%s != %s)" \
            % (system_jobs_pg.results[0].id, cleanup_jobs_pg.id)

        # calculate number of remaining jobs
        number_special_cases = len(filter(lambda x: x.type in ('project_update', 'inventory_update'), multiple_jobs_with_status_completed))
        expected_number_remaining_jobs = number_special_cases + system_jobs_pg.count

        # assess remaming unified jobs
        unified_jobs_pg = api_unified_jobs_pg.get()
        assert unified_jobs_pg.count == expected_number_remaining_jobs, "Unexpected number of unified_jobs returned \
            (unified_jobs_pg.count: %s != expected_number_remaining_jobs: %s)" % (unified_jobs_pg.count, expected_number_remaining_jobs)

    def test_cleanup_deleted(self, tmpdir, old_deleted_object, cleanup_deleted_template, ansible_runner):
        '''
        Creates and deletes different types of objects, runs cleanup_deleted, and then verifies that
        objects are deleted.
        '''
        # launch job first time
        payload = dict(extra_vars=dict(days=365))
        system_jobs_pg = cleanup_deleted_template.launch(payload)

        # wait for cleanup to finish
        system_jobs_pg.wait_until_completed()

        # assert success
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert something deleted
        match = re.search(r'^Removed (\d+) items', system_jobs_pg.result_stdout, re.MULTILINE)
        assert match, "Unexpected output from system job - %s" % system_jobs_pg
        assert int(match.group(1)) == 1, "Unexpected number of deleted objects (%s)" % match.group(1)

        # launch job second time
        payload = dict(extra_vars=dict(days=365))
        system_jobs_pg = cleanup_deleted_template.launch(payload)

        # assert success
        system_jobs_pg.wait_until_completed()
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert that nothing was deleted on the second job run
        match = re.search(r'^Removed (\d+) items', system_jobs_pg.result_stdout, re.MULTILINE)
        assert match, "Unexpected output from system job - %s" % system_jobs_pg
        assert int(match.group(1)) == 0, "Unexpected number of deleted objects (%s)" % match.group(1)

    def test_cleanup_activitystream(self, cleanup_activitystream_template, multiple_jobs_with_status_completed, api_activity_stream_pg):
        '''
        Launch jobs of different types, run cleanup activitystreams, and verify that the activitystream is cleared.
        '''
        # pretest
        activity_stream_pg = api_activity_stream_pg.get()
        assert activity_stream_pg.count != 0, "Activity stream empty (%s == 0)." % activity_stream_pg.count

        # launch job
        payload = dict(extra_vars=dict(days=0))
        system_jobs_pg = cleanup_activitystream_template.launch(payload)

        # wait 25 minutes for cleanup to finish
        system_jobs_pg.wait_until_completed(timeout=60 * 25)

        # assess success
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert that activity_stream is cleared
        activity_stream_pg = api_activity_stream_pg.get()
        assert activity_stream_pg.count == 0, "After running cleanup_activitystream, " \
            "activity_stream data is still present (count == %s)" \
            % activity_stream_pg.count

    @pytest.mark.skipif(True, reason="Not yet implemented")
    def test_cleanup_facts(self, cleanup_facts_template):
        '''
        Launch a cleanup_facts job and assert desired facts have been deleted.
        '''
        # assert facts exist

        # launch job
        payload = dict(extra_vars=dict(granularity='0d', older_than='0d'))
        system_jobs_pg = cleanup_facts_template.launch(payload)

        # wait 2 minutes for cleanup to finish
        system_jobs_pg.wait_until_completed(timeout=60 * 2)

        # assess success
        assert system_jobs_pg.is_successful, "Job unsuccessful - %s" % system_jobs_pg

        # assert facts have been removed
