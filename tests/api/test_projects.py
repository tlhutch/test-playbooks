"""# Create projects in /var/lib/awx/projects and verify
# 1) projects starting with '.' or '_' are excluded from config['project_local_paths']
# 2) project appears under config['project_local_paths']
"""

import os
import logging

import towerkit.exceptions as exc
from towerkit.utils import poll_until, random_title

import pytest
import fauxfactory

from tests.api import APITest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def project_with_queued_updates(project_ansible_playbooks_git_nowait):
    # Initiate several project updates
    update_pg = project_ansible_playbooks_git_nowait.get_related('update')
    for i in range(4):
        update_pg.post({})
    return project_ansible_playbooks_git_nowait


@pytest.fixture(scope="function")
def project_with_galaxy_requirements(factories):
    return factories.project(
        name="project-with-galaxy-requirements - %s" % fauxfactory.gen_utf8(),
        scm_type='git',
        scm_url='https://github.com/ansible/test-playbooks',
        scm_branch='with_requirements'
    )


@pytest.mark.usefixtures('authtoken')
class Test_Projects(APITest):

    def check_secret_fields(self, string_to_check, *secrets):
        for secret in secrets:
            assert secret not in string_to_check

    def get_project_update_galaxy_update_task(self, project, job_type='run'):
        task_icontains = "fetch galaxy roles from requirements.yml"
        res = project.related.project_updates.get(job_type=job_type, order_by='-created') \
                                             .results[0].related.events \
                                             .get(task__icontains=task_icontains, event__startswith='runner_on_', order_by='counter')

        _res = [result for result in res['results'] if result['event'] != 'runner_on_start']

        assert 2 == len(_res), \
                "Expected to find 2 job events matching task={},event__startswith={} for project update {}".format(
                        task_icontains, 'runner_on_', project.related.last_update)
        return (_res)

    @pytest.mark.parametrize('scm_type', ['git', 'hg', 'svn'])
    def test_project_update_basics(self, factories, scm_type):
        project = factories.project(name='Basic {} project {}'.format(scm_type, random_title()), scm_type=scm_type)
        assert project.status == 'successful'
        assert project.scm_revision
        assert project.summary_fields.last_update
        assert project.scm_type == scm_type
        assert str(project.id) in project.local_path
        assert project.last_updated == project.last_job_run

    @pytest.mark.parametrize('scm_type, playbook, before, after, expect_method', [
        (
            'git',
            'utf-8.yml',
            'a6b66f248c1819e9644112645ad043e96c57e94e',  # short: a6b66f2
            'e11c99d1098ceaff44d8830546f03a12d16bf238',
            lambda x: x
        ),
        (
            'hg',
            'utf-8.yml',
            'e025df47a1d000c98a1f71932708ddaedf929452',  # short: e025df4
            '5139fc9da4f3f79f689b6b56fd5b658d9e5c2eeb',
            lambda x: x[:12]  # not consistent
        ),
        (
            'svn',
            'trunk/utf-8.yml',
            'r9',  # short: 9,
            'r10',
            lambda x: x.strip('r')
        )
    ], ids=['git', 'hg', 'svn'])
    def test_project_update_specific_commit(self, factories, active_instances,
                                            scm_type, playbook, before, after, expect_method):
        # assure it runs on same instance every time
        org = factories.organization()
        ig = factories.instance_group()
        ig.add_instance(active_instances.results.pop())
        org.add_instance_group(ig)
        project = factories.project(
            name='Commit checkout {} project {}'.format(scm_type, random_title()),
            scm_type=scm_type, scm_branch=before, organization=org)
        poll_until(lambda: hasattr(project.get().related, 'last_update'), timeout=30)
        project.related.last_update.get().wait_until_completed().assert_successful()
        assert project.scm_type == scm_type
        # the saved version of the commit follows some reliable syntax pattern
        assert project.scm_revision == expect_method(before)
        # current checkout is before playbook was added
        assert playbook not in list(project.get_related('playbooks'))

        project.scm_branch = after
        update = project.get_related(
            'project_updates', order_by='-created', status__in='pending,waiting,running'
        ).results.pop()
        update.wait_until_completed().assert_successful()
        project.get()
        assert project.scm_revision == expect_method(after)
        # playbook was added in last comment
        assert playbook in list(project.get_related('playbooks'))

    def test_manual_project(self, skip_if_cluster, project_ansible_playbooks_manual):
        """Verify tower can successfully creates a manual project (scm_type='').
        This includes verifying UTF-8 local-path.
        """
        # if we make it through the fixure, post worked
        # assert various project attributes are empty ('')
        for attr in ('scm_type', 'scm_url', 'scm_branch'):
            assert hasattr(project_ansible_playbooks_manual, attr), \
                "Unhandled project attribute: %s" % attr
            attr_value = getattr(project_ansible_playbooks_manual, attr)
            assert attr_value == '', \
                "Unexpected project.%s (%s != %s)" % \
                (attr, attr_value, '')

        # assert various project attributes are false
        for attr in ('scm_clean', 'scm_delete_on_update', 'last_job_failed',
                     'scm_update_on_launch', 'last_update_failed',):

            assert hasattr(project_ansible_playbooks_manual, attr), \
                "Unhandled project attribute: %s" % attr
            attr_value = getattr(project_ansible_playbooks_manual, attr)
            assert attr_value is False, \
                "Unexpected project.%s (%s != %s)" % \
                (attr, attr_value, False)

        # assert related.update.can_update == false
        update_pg = project_ansible_playbooks_manual.get_related('update')
        assert not update_pg.json['can_update'], \
            "Manual project incorrectly has can_update:%s" % \
            (update_pg.json['can_update'],)

        # assert related.project_updates.count == 0
        for related_attr in ('project_updates', 'schedules'):
            related_pg = project_ansible_playbooks_manual.get_related(related_attr)
            assert related_pg.count == 0, \
                "A manual project has %d %s, but should have %d %s" % \
                (related_pg.count, related_attr, 0, related_attr)

    # Override the project local_path to workaround unicode issues
    @pytest.mark.fixture_args(local_path="project_dir_%s" % fauxfactory.gen_alphanumeric())
    def test_change_from_manual_to_scm_project(self, skip_if_cluster, project_ansible_playbooks_manual):
        """Verify tower can successfully convert a manual project, into a scm
        managed project.
        """
        # change the scm_type to 'git'
        project_pg = project_ansible_playbooks_manual.patch(
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks.git',
        )

        # update the project and wait for completion
        latest_update_pg = project_pg.update().wait_until_completed()

        # assert project_update was successful
        latest_update_pg.assert_successful()

        # update the project endpoint
        project_pg.get()

        # assert project is marked as successful
        project_pg.assert_successful()

    # Skip for Openshift because of Github Issue: https://github.com/ansible/tower-qa/issues/2591
    def test_automatic_deletion_of_project_folder(self, skip_if_openshift, factories, ansible_adhoc, api_config_pg, api_ping_pg, v2):
        project = factories.project()
        expected_project_path = os.path.join(api_config_pg.project_base_dir, project.local_path)  # absolute path

        # Test has 2 variations - standalone and cluster
        all_instances = set(inst.hostname for inst in v2.instances.get(
            capacity__gt=0, page_size=200, rampart_groups__controller__isnull=True
        ).results)
        update = project.get_related('last_update')
        instances = set([update.execution_node])
        if len(all_instances) > 1:
            # Update project on 2nd instance, to validate broadcasted task
            inst2 = v2.instances.get(
                not__hostname=update.execution_node,
                capacity__gt=0, page_size=200, rampart_groups__controller__isnull=True
            ).results.pop()
            ig = factories.instance_group()
            ig.add_instance(inst2)
            jt = factories.job_template(project=project)
            jt.add_instance_group(ig)  # JT run forces full checkout
            job = jt.launch().wait_until_completed()
            assert job.execution_node not in instances
            instances.add(job.execution_node)

        contacted = ansible_adhoc()['tower'].stat(path=expected_project_path)

        inventory_instances = set([])  # inventory node names different from API names
        for host, result in contacted.items():
            if 'stat' not in result:
                raise Exception('Connection to {} failed result: {}'.format(host, result))
            if result['stat']['exists']:
                inventory_instances.add(host)
        assert len(inventory_instances) == len(instances), 'Found project folder {} in unexpected number of nodes'.format(
            expected_project_path
        )

        project.delete()

        # project folder should now not exist in any instances
        def folder_has_been_deleted_everywhere():
            contacted = ansible_adhoc()['tower'].stat(path=expected_project_path)
            not_deleted = []
            for host, result in contacted.items():
                if result['stat']['exists']:
                    not_deleted.append(host)
            if not_deleted:
                log.warning('Project folder {} still exists on {}'.format(expected_project_path, not_deleted))
                return False
            return True

        # it may take a while for the task to delete the folder to complete
        poll_until(folder_has_been_deleted_everywhere, timeout=30)

    @pytest.mark.ansible_integration
    def test_update_with_private_git_repository(self, skip_if_cluster, ansible_runner, api_config_pg, project_ansible_docsite_git):
        """Tests that project updates succeed with private git repositories."""
        # find project path
        local_path = project_ansible_docsite_git.local_path
        expected_project_path = os.path.join(api_config_pg.project_base_dir, local_path)

        # assert project directory created
        contacted = ansible_runner.stat(path=expected_project_path)
        for result in contacted.values():
            assert result['stat']['exists'], "The expected project directory was not found (%s)." % \
                expected_project_path

    @pytest.mark.parametrize('timeout, status, job_explanation', [
        (0, 'successful', ''),
        (60, 'successful', ''),
        (1, 'failed', 'Job terminated due to timeout'),
    ], ids=['no timeout', 'under timeout', 'over timeout'])
    def test_update_with_timeout(self, project, timeout, status, job_explanation):
        """Tests project updates with timeouts."""
        project.patch(timeout=timeout)

        # launch project update and assess spawned update
        update_pg = project.update().wait_until_completed()
        assert update_pg.status == status, \
            "Unexpected project update status. Expected '{0}' but received '{1}.'".format(status, update_pg.status)
        assert update_pg.job_explanation == job_explanation, \
            "Unexpected update job_explanation. Expected '{0}' but received '{1}.'".format(job_explanation, update_pg.job_explanation)
        assert update_pg.timeout == project.timeout, \
            "Update_pg has a different timeout value ({0}) than its project ({1}).".format(update_pg.timeout, project.timeout)

    @pytest.mark.parametrize("scm_type,mod_kwargs", [
        ('hg', {'scm_branch': '09e81486069b4e38e62c24d7d7a529fc975d4a31'}),
        ('git', {'scm_branch': 'with_requirements'}),
        ('hg', {'scm_type': 'git', 'scm_url': 'https://github.com/ansible/test-playbooks.git'}),
        ('git', {'scm_url': 'https://github.com/alancoding/ansible-playbooks.git'})
    ], ids=['hg-branch', 'git-branch', 'scm_type', 'git-url'])
    def test_auto_update_on_modification_of_scm_fields(self, factories, scm_type, mod_kwargs):
        project = factories.project(scm_type=scm_type)
        assert project.related.project_updates.get().count == 1

        # verify that changing update-relevant parameters causes new update
        project.patch(**mod_kwargs)
        assert project.related.project_updates.get().count == 2

    def test_cancel_queued_update(self, project_ansible_git_nowait):
        """Verify the project->current_update->cancel endpoint behaves as expected when canceling a
        queued project_update.  Note, the project_ansible_git repo is used
        because the repo is large enough that the git-clone should take enough
        time to trigger a project_update cancel.
        """
        update_pg = project_ansible_git_nowait.get_related('current_update')
        cancel_pg = update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel project_update (can_cancel:%s)" % cancel_pg.can_cancel

        # cancel job
        cancel_pg.post()

        # wait for project_update to complete
        update_pg = update_pg.wait_until_completed()

        # assert project_update status is canceled
        assert update_pg.status == 'canceled', "Unexpected project_update " \
            "status after cancelling project update (expected status:canceled) " \
            "- %s" % update_pg

        # update project resource
        project_ansible_git_nowait = project_ansible_git_nowait.wait_until_completed()

        # assert project status is failed
        assert project_ansible_git_nowait.status == 'canceled', \
            "Unexpected project status after cancelling project update" \
            "(expected status:canceled) - %s" % project_ansible_git_nowait

    def test_cancel_running_update(self, project_ansible_git_nowait):
        """Verify the project->current_update->cancel endpoint behaves as expected
        when canceling a running project_update.  Note, the project_ansible_git
        repo is used because the repo is large enough that the git-clone should
        take enough time to trigger a project_update cancel.
        """
        update_pg = project_ansible_git_nowait.get_related('current_update')
        cancel_pg = update_pg.get_related('cancel')
        assert cancel_pg.can_cancel, "Unable to cancel project_update (can_cancel:%s)" % cancel_pg.can_cancel

        # wait for project_update to be running
        update_pg = update_pg.wait_until_status('running')

        # cancel job
        cancel_pg.post()

        # wait for project_update to complete
        # ansible.git includes submodules, which can take time to update
        update_pg = update_pg.wait_until_completed(timeout=60 * 4)

        # assert project_update status is canceled
        assert update_pg.status == 'canceled', "Unexpected project_update " \
            "status after cancelling project update (expected status:canceled) " \
            "- %s" % update_pg

        # update project resource
        project_ansible_git_nowait = project_ansible_git_nowait.wait_until_completed()

        # assert project status is failed
        assert project_ansible_git_nowait.status == 'canceled', "Unexpected " \
            "project status after cancelling project update (expected " \
            "status:canceled) - %s" % project_ansible_git_nowait

    def test_update_cascade_delete(self, project_ansible_playbooks_git, api_project_updates_pg):
        """Verify that associated project updates get cascade deleted with project
        deletion.
        """
        project_id = project_ansible_playbooks_git.id

        # assert that we have a project update
        assert api_project_updates_pg.get(project=project_id).count == 1, \
            "Unexpected number of project updates. Expected one update."

        # delete project and assert that project updates deleted
        project_ansible_playbooks_git.delete()
        assert api_project_updates_pg.get(project=project_id).count == 0, \
            "Unexpected number of project updates after deleting project. Expected zero updates."

    def test_conflict_exception_with_running_project_update(self, factories):
        project = factories.project()
        update = project.update()

        with pytest.raises(exc.Conflict) as e:
            project.delete()
        assert e.value[1] == {'error': 'Resource is being used by running jobs.', 'active_jobs': [{'type': 'project_update', 'id': update.id}]}

        update.wait_until_completed().assert_successful()
        project.get().assert_successful()

    def test_delete_related_fields(self, project_ansible_playbooks_git):
        """Verify that related fields on a deleted resource respond as expected"""
        # delete all the projects
        project_ansible_playbooks_git.delete()

        # assert related resources are notfound (404)
        for related in ('last_job', 'last_update', 'schedules', 'activity_stream', 'project_updates', 'teams', 'playbooks', 'update'):
            with pytest.raises(exc.NotFound):
                assert project_ansible_playbooks_git.get_related(related)

    @pytest.mark.ansible_integration
    def test_project_with_galaxy_requirements(self, skip_if_cluster, factories, ansible_runner, project_with_galaxy_requirements):
        """Verify that project requirements are downloaded when specified in a requirements file."""
        # create a JT with our project and launch a job with this JT
        job_template_pg = factories.job_template(
            project=project_with_galaxy_requirements,
            playbook="sleep.yml",
            extra_vars=dict(sleep_interval=60*3)
        )
        job_template_pg.ds.inventory.add_host()
        # keep job running so files will be in place while we shell in
        job_pg = job_template_pg.launch()

        # The job cwd is not populated until prep is finished, which happens after
        # it is changed to running status, but before events come in...
        poll_until(lambda: job_pg.get_related('job_events').count, timeout=30)
        job_pg = job_pg.get()  # job_cwd is only in detail view

        # assert that expected galaxy requirements were downloaded
        # wherever the job runs, that is where the roles should be
        expected_role_path = os.path.join(job_pg.job_cwd, "roles/yatesr.timezone")
        contacted = ansible_runner.stat(path=expected_role_path)
        for result in contacted.values():
            assert result['stat']['exists'], "The expected galaxy role requirement was not found (%s)." % \
                expected_role_path

    def test_project_with_galaxy_requirements_processed_on_scm_change(self, factories):
        project_with_requirements = factories.project(scm_url='https://github.com/ansible/test-playbooks.git',
                                                         scm_branch='with_requirements')
        jt_with_requirements = factories.job_template(project=project_with_requirements,
                                                         playbook='debug.yml')

        jt_with_requirements.launch().wait_until_completed().assert_successful(
            msg="First job template run for a project always triggers the processing of requirements.yml"
            )
        project_with_requirements.update().wait_until_completed().assert_successful(msg="Project update that pulls down newly written SCM commits failed.")

        jt_with_requirements.launch().wait_until_completed().assert_successful(msg="Job Template that triggers SCM update that processes requirements.yml failed")
        (event_unforced, event_forced) = self.get_project_update_galaxy_update_task(project_with_requirements)

        assert 'runner_on_ok' in [event_unforced.event, event_forced.event]

    @pytest.mark.parametrize("scm_url, use_credential",
                             [('https://github.com/ansible/tower.git', True),
                              ('https://github.com/ansible/test-playbooks.git', True),
                              ('https://foobar:barfoo@github.com/ansible/tower.git', False)],
                             ids=['invalid_cred', 'valid_cred', 'cred_in_url'])
    def test_project_update_results_do_not_leak_credential(self, factories, scm_url, use_credential):
        if use_credential:
            cred = factories.credential(kind='scm', username='foobar', password='barfoo')
        else:
            cred = None
        project = factories.project(credential=cred, scm_url=scm_url)
        pu = project.related.project_updates.get().results.pop()
        assert pu.is_completed

        self.check_secret_fields(pu.result_stdout, 'foobar', 'barfoo')
        events = pu.related.events.get(page_size=200).results
        for event in events:
            self.check_secret_fields(event.stdout, 'foobar', 'barfoo')
            self.check_secret_fields(str(event.event_data), 'foobar', 'barfoo')

    @pytest.mark.ansible_integration
    def test_git_project_from_file_path(self, git_file_path, factories):
        """Confirms that local file paths can be used for git repos"""
        project = factories.project(scm_url=git_file_path)
        project.assert_successful()
        assert project.scm_revision
