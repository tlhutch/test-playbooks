import logging

import pytest

import fauxfactory

from tests.api import APITest

from awxkit.utils import random_title
from awxkit.exceptions import BadRequest


log = logging.getLogger(__name__)


@pytest.mark.usefixtures('authtoken')
class TestJobTemplateBranchOverride(APITest):

    GIT_CONFIG_COMMANDS = [
        'git config user.email jenkins@ansible.com',
        'git config user.name DoneByTest'
    ]

    @staticmethod
    def verify_cmd_success(contacted):
        for result in contacted.values():
            assert 'rc' in result, result
            assert result['rc'] == 0, result

    def test_job_template_new_branch_git(self, git_file_path, ansible_adhoc, factories):
        project = factories.project(
            name='Local dir with a unique branch {}'.format(random_title()),
            scm_url=git_file_path, allow_override=True)
        assert project.allow_override is True  # sanity

        # set up source repo
        ansible_module = ansible_adhoc().tower
        local_path = git_file_path[len('file://'):]
        branch_name = random_title(non_ascii=False)
        tmp_filename = random_title(non_ascii=False) + '.yml'
        run_these = self.GIT_CONFIG_COMMANDS + [
            'git checkout -b {}'.format(branch_name)
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        jt = factories.job_template(
            name='Uses non-default branch {}'.format(random_title()),
            project=project, scm_branch=branch_name, playbook=tmp_filename)
        assert jt.scm_branch == branch_name  # sanity

        # branch exists, but the expected file is not commited to it, so should fail
        job1 = jt.launch().wait_until_completed()
        job1.assert_status('failed')
        assert 'the playbook: {} could not be found'.format(tmp_filename) in job1.result_stdout

        # If a change is made to the branch and the job is launched again
        # then, by design, it must pick up the changes that were made to the branch
        # because non-default branches do not save revision
        run_these = [
            'cp {} {}'.format('debug.yml', tmp_filename),
            'git add .',
            'git commit -m "Adding temporary playbook {}"'.format(tmp_filename),
            'git checkout master'
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        job2 = jt.launch().wait_until_completed()
        job2.assert_successful()  # will fail if playbook does not exist

    def test_jt_specifies_branch_disable_project_allow_override(self, factories):
        project = factories.project(
            scm_url='https://github.com/ansible/test-playbooks',
            scm_type='git',
            allow_override=False
        )

        # Check that we can update allow_override
        project.allow_override = True
        assert project.allow_override is True

        jt = factories.job_template(project=project, scm_branch='empty_branch', playbook='foobar.yml')

        with pytest.raises(BadRequest) as e:
            project.allow_override = False

        assert 'allow_override' in e.value[1], f'No error thrown for setting "allow_overide" to false when project already has a job template specifying a branch! Found {e.value[1]} instead'
        assert f'One or more job templates depend on branch override behavior for this project (ids: {jt.id}).' in e.value[1]['allow_override'], f'Unexpected error message, found {e.value[1]["allow_override"]}'

    def test_jt_revoke_override(self, factories):
        project = factories.project(allow_override=True)
        assert project.allow_override
        factories.job_template(project=project)  # does not use this feature
        project.allow_override = False  # does not raise error

    def test_job_template_branch_hg(self, factories):
        # Branches in this repo: default, foobar, no_roles
        # the foobar branch has foobar.yml playbook
        project = factories.project(
            scm_url='https://AlanCoding@bitbucket.org/AlanCoding/ansible-roles-example-hg',
            scm_type='hg',
            allow_override=True
        )

        jt = factories.job_template(project=project, scm_branch='foobar', playbook='foobar.yml')

        job = jt.launch().wait_until_completed()
        job.assert_successful()  # will fail if playbook does not exist

    @pytest.mark.parametrize(
        'scm_type, scm_url',
        [
            ('hg', 'https://bitbucket.org/ansibleengineering/test-playbooks-hg'),
            ('svn', 'https://github.com/ansible/test-playbooks')
        ]
    )
    def test_non_git_projects_do_not_accept_scm_refspec(self, factories, scm_type, scm_url):
        # The refspec option for svn and hg is invalid, test that it raises a BadRequest option
        with pytest.raises(BadRequest) as e:
            factories.project(
                scm_url=scm_url,
                scm_type=scm_type,
                scm_refspec="refs/pull/1/HEAD",
                allow_override=True
            )

        assert 'scm_refspec' in e.value[1], f'No error thrown for "scm_refspec"! Found {e.value[1]} instead'
        assert 'SCM refspec can only be used with git projects.' in e.value[1]['scm_refspec'], f'Unexpected error message, found {e.value[1]["scm_refspec"]}'

    def test_job_template_branch_svn(self, factories):
        # Branches in default repo are same as git: master, inventory_additions, with_requirements
        project = factories.project(scm_type='svn', allow_override=True)

        # we cannot checkout branches in svn, only switch revision
        # this switches to a revision before the become.yml playbook was added
        jt = factories.job_template(project=project, scm_branch='r9', playbook='become.yml')

        job = jt.launch().wait_until_completed()
        job.assert_status('failed')
        assert 'the playbook: become.yml could not be found' in job.result_stdout

    def test_project_allow_override_false_and_jt_scm_branch(self, factories):
        project = factories.project(
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
            scm_branch='',
            allow_override=False
        )
        with pytest.raises(BadRequest) as e:
            factories.job_template(project=project, scm_branch='empty_branch')

        assert 'scm_branch' in e.value[1], f'No error thrown for "scm_branch" when project does not allow override! Found {e.value[1]} instead'
        assert 'Project does not allow overriding branch.' in e.value[1]['scm_branch'], f'Unexpected error message, found {e.value[1]["scm_branch"]}'

    def test_project_branch_with_missing_playbook(self, factories):
        project = factories.project(
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
            scm_branch='devel',
            allow_override=True
        )

        try:
            factories.job_template(project=project, scm_branch='empty_branch', playbook='sleep.yml')
        except BadRequest as e:
            pytest.fail(f'unexpected BadRequest exception raised: {e.value[1]}')

        project = factories.project(
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
            scm_branch='devel',
            allow_override=False
        )

        with pytest.raises(BadRequest) as e:
            factories.job_template(project=project, scm_branch='empty_branch', playbook='sleep.yml')

        assert 'playbook' in e.value[1], f'No error thrown for "playbook" when project does not allow override and the playbook is missing! Found {e.value[1]} instead'
        assert 'Playbook not found for project.' in e.value[1]['playbook'], f'Unexpected error message, found {e.value[1]["playbook"]}'

    def test_job_template_ask_scm_branch_on_launch_and_job_specifies_scm_branch(self, factories):
        project = factories.project(
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
            scm_branch='empty_branch',
            allow_override=True
        )

        jt = factories.job_template(
            project=project,
            ask_scm_branch_on_launch=True
        )
        job = jt.launch(dict(scm_branch='empty_branch'))

        job.wait_until_completed()

        prompts = job.get_related('create_schedule').prompts
        assert not prompts

    @pytest.mark.parametrize('identifier',
        ['with_requirements', '31ddc6c1ce8532e947763c38b4751772bb85e207'],
        ids=['branch', 'commit']
    )
    def test_detection_of_roles_in_branches(self, factories, identifier):
        project = factories.project(
            name="project-may-or-may-not-have-galaxy-requirements - %s" % fauxfactory.gen_utf8(),
            scm_type='git',
            scm_url='https://github.com/ansible/test-playbooks',
            scm_branch='',
            allow_override=True
        )
        jt1 = factories.job_template(project=project)
        jt1.ds.inventory.add_host()

        jt1.launch().wait_until_completed().assert_successful()

        # assure that job1 does not fool job2 into thinking there are no galaxy req
        jt2 = factories.job_template(
            project=project,
            playbook='use_debug_role.yml',
            scm_branch=identifier,
            inventory=jt1.ds.inventory
        )
        jt2.launch().wait_until_completed().assert_successful()

    def test_job_template_non_default_commit(self, git_file_path, ansible_adhoc, factories):
        '''Test using a commit from a branch which is not the main branch
        '''
        project = factories.project(
            name='Local dir with a unique branch {}'.format(random_title()),
            scm_url=git_file_path, allow_override=True)

        # set up source repo
        ansible_module = ansible_adhoc().tower
        local_path = git_file_path[len('file://'):]
        tmp_filename = random_title(non_ascii=False) + '.yml'
        run_these = self.GIT_CONFIG_COMMANDS + [
            'git checkout -b arbitrary_branch_name',
            'cp {} {}'.format('debug.yml', tmp_filename),
            'git add .',
            'git commit -m "Adding temporary playbook {}"'.format(tmp_filename),
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        contacted = ansible_module.shell('git rev-parse HEAD', chdir=local_path)
        result = contacted.values().pop()
        assert 'stdout' in result, result
        commit = result['stdout']
        # assert that any other nodes in cluster also have same stuff
        assert all(r.get('stdout', None) == commit for r in contacted.values())

        contacted = ansible_module.shell('git checkout master', chdir=local_path)
        self.verify_cmd_success(contacted)

        jt = factories.job_template(
            name='Uses commit in non-default branch {}'.format(random_title()),
            project=project, scm_branch=commit, playbook=tmp_filename)

        job = jt.launch().wait_until_completed()
        assert job.scm_revision == commit
        job.assert_successful()  # will fail if playbook does not exist

    def test_commit_and_branch_name_conflict(self, git_file_path, ansible_adhoc, factories):
        project = factories.project(
            name='Local dir branch and commit name conflict {}'.format(random_title()),
            scm_url=git_file_path, allow_override=True
        )

        # run the JT so we make the project folder dirty with old data
        jt = factories.job_template(project=project, playbook='debug.yml')
        jt.ds.inventory.add_host()
        jt.launch().wait_until_completed().assert_successful()

        # obtain the latest commit of the repo
        ansible_module = ansible_adhoc().tower
        local_path = git_file_path[len('file://'):]
        contacted = ansible_module.shell('git rev-parse HEAD', chdir=local_path)
        self.verify_cmd_success(contacted)
        commit = None
        for result in contacted.values():
            assert 'stdout' in result, result
            if commit:
                assert result['stdout'] == commit
            else:
                commit = result['stdout']
        assert commit

        # checkout a new branch with a similar name to the commit and add content
        tmp_filename = random_title(non_ascii=False) + '.yml'
        run_these = self.GIT_CONFIG_COMMANDS + [
            'git checkout -b {}'.format(commit[:5]),
            'cp {} {}'.format('debug.yml', tmp_filename),
            'git add .',
            'git commit -m "Adding temporary playbook {}"'.format(tmp_filename)
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        # now run a job template against the _branch_ and expect the file to be there
        jt2 = factories.job_template(project=project, playbook=tmp_filename, scm_branch=commit[:5], inventory=jt.ds.inventory)
        jt2.launch().wait_until_completed().assert_successful()

    def test_job_template_prompt_multiple_commits(self, git_file_path, ansible_adhoc, factories):
        '''Test providing different commits
        '''
        project = factories.project(
            name='Local dir with new commits {}'.format(random_title()),
            scm_url=git_file_path, allow_override=True
        )

        # set up source repo
        ansible_module = ansible_adhoc().tower
        local_path = git_file_path[len('file://'):]
        tmp_filename1 = random_title(non_ascii=False) + '.yml'
        run_these = self.GIT_CONFIG_COMMANDS + [
            'git checkout -b arbitrary_branch_name',
            'cp {} {}'.format('debug.yml', tmp_filename1),
            'git add .',
            'git commit -m "Adding temporary playbook {}"'.format(tmp_filename1)
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        contacted = ansible_module.shell('git rev-parse HEAD', chdir=local_path)
        result = contacted.values().pop()
        assert 'stdout' in result, result
        commit_a = result['stdout']

        tmp_filename2 = random_title(non_ascii=False) + '.yml'
        run_these = [
            'git rm {}'.format(tmp_filename1),
            'cp {} {}'.format('debug.yml', tmp_filename2),
            'git add .',
            'git commit -m "Removing {} and adding {}"'.format(tmp_filename1, tmp_filename2)
        ]
        for this_command in run_these:
            contacted = ansible_module.shell(this_command, chdir=local_path)
            self.verify_cmd_success(contacted)

        contacted = ansible_module.shell('git rev-parse HEAD', chdir=local_path)
        result = contacted.values().pop()
        assert 'stdout' in result, result
        commit_b = result['stdout']

        contacted = ansible_module.shell('git checkout master', chdir=local_path)
        self.verify_cmd_success(contacted)

        # reuse inventory just so that we do not recreate it
        inventory = factories.inventory()

        jt1 = factories.job_template(
            name='Uses tmp file {} for playbook: {}'.format(tmp_filename1, random_title()),
            project=project, inventory=inventory, ask_scm_branch_on_launch=True,
            playbook=tmp_filename1,
            allow_simultaneous=True
        )
        assert jt1.ask_scm_branch_on_launch is True  # sanity
        # Launch jobs to run simultaneously
        job1a = jt1.launch(dict(scm_branch=commit_a))
        job1b = jt1.launch(dict(scm_branch=commit_b)).wait_until_completed()
        job1a.wait_until_completed()
        for field in ('scm_branch', 'scm_revision'):
            assert (commit_a, commit_b) == (getattr(job1a, field), getattr(job1b, field))
        job1a.assert_successful()
        job1b.assert_status('failed')

        jt2 = factories.job_template(
            name='Uses tmp file {} for playbook: {}'.format(tmp_filename2, random_title()),
            project=project, inventory=inventory, ask_scm_branch_on_launch=True,
            playbook=tmp_filename2,
            allow_simultaneous=True
        )

        # Launch jobs to run simultaneously
        job2a = jt2.launch(dict(scm_branch=commit_a))
        job2b = jt2.launch(dict(scm_branch=commit_b)).wait_until_completed()
        job2a.wait_until_completed()
        for field in ('scm_branch', 'scm_revision'):
            assert (commit_a, commit_b) == (getattr(job2a, field), getattr(job2b, field))
        job2a.assert_status('failed')
        job2b.assert_successful()

    def test_workflow_job_node_can_pass_through_scm_branch_if_promptable(self, factories):
        project = factories.project(allow_override=True)
        host = factories.host()
        # run the JT so we make the project folder dirty with old data
        jt_prompt = factories.job_template(
            project=project,
            playbook='debug.yml',
            inventory=host.related.inventory.get(),
            ask_scm_branch_on_launch=True
            )

        jt_no_prompt = factories.job_template(
            project=project,
            playbook='debug.yml',
            inventory=host.related.inventory.get(),
            )
        wfjt = factories.workflow_job_template()
        with pytest.raises(BadRequest) as e:
            wfjt.get_related('workflow_nodes').post(dict(
                scm_branch='foo',
                unified_job_template=jt_no_prompt.id,
            ))
        assert 'scm_branch' in e.value[1], f"Did not raise error for attempting to provide scm_branch! {e.value[1]}"
        assert 'Field is not configured to prompt on launch.' in e.value[1]['scm_branch'], f"Error message was unexpected. Error message: {e.value[1]}"
        prompt_branch = 'foo_does_not_exist'
        wfjt.get_related('workflow_nodes').post(dict(
            scm_branch=prompt_branch,
            unified_job_template=jt_prompt.id,
        ))

        wf_job = wfjt.launch().wait_until_completed()
        # Should fail because branch does not exist
        wf_job.assert_status('failed')
        wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
        job = wf_job_node.related.job.get()
        assert job.scm_branch == prompt_branch

    def test_workflow_job_template_promptable(self, factories):
        project = factories.project(allow_override=True)
        host = factories.host()
        jt_prompt = factories.job_template(
            project=project,
            playbook='debug.yml',
            inventory=host.related.inventory.get(),
            ask_scm_branch_on_launch=True
            )

        wfjt = factories.workflow_job_template(scm_branch='wfjt_branch', ask_scm_branch_on_launch=True)
        assert wfjt.scm_branch == 'wfjt_branch'  # sanity
        assert wfjt.ask_scm_branch_on_launch is True  # sanity

        node = factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=jt_prompt,
            scm_branch='wfjt_node_branch'
        )
        assert node.scm_branch == 'wfjt_node_branch'  # sanity

        # launch and verify with just the WFJT value
        wf_job = wfjt.launch().wait_until_completed()
        assert wf_job.scm_branch == 'wfjt_branch'  # sanity
        wf_job.assert_status('failed')  # Should fail because branch does not exist
        wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
        job = wf_job_node.related.job.get()
        assert job.scm_branch == 'wfjt_branch'

        wf_job = wfjt.launch(payload=dict(scm_branch='wfjt_prompt_branch')).wait_until_completed()
        assert wf_job.scm_branch == 'wfjt_prompt_branch'  # sanity
        wf_job.assert_status('failed')  # Should fail because branch does not exist
        wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
        job = wf_job_node.related.job.get()
        assert job.scm_branch == 'wfjt_prompt_branch'

        # Test that these attrs are updatable
        wfjt.scm_branch = 'foo'
        assert wfjt.scm_branch == 'foo'
        wfjt.ask_scm_branch_on_launch = False
        assert wfjt.ask_scm_branch_on_launch is False

    def test_workflow_job_template_promptable_non_promptable_jt(self, factories):
        project = factories.project(allow_override=True)
        host = factories.host()
        jt_prompt = factories.job_template(
            project=project,
            playbook='debug.yml',
            inventory=host.related.inventory.get(),
            ask_scm_branch_on_launch=False,
            scm_branch='fake_branch'
            )

        wfjt = factories.workflow_job_template(scm_branch='wfjt_branch', ask_scm_branch_on_launch=True)
        assert wfjt.scm_branch == 'wfjt_branch'  # sanity
        assert wfjt.ask_scm_branch_on_launch is True  # sanity

        factories.workflow_job_template_node(
            workflow_job_template=wfjt,
            unified_job_template=jt_prompt,
        )
        # Verify the WFJT value is not passed to a non-promtable JT
        wf_job = wfjt.launch().wait_until_completed()
        assert wf_job.scm_branch == 'wfjt_branch'  # sanity
        wf_job.assert_status('failed')  # Should fail because branch does not exist
        wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
        job = wf_job_node.related.job.get()
        assert job.scm_branch == 'fake_branch'

        # Verify the WFJT launch scm_branch argument is not passed to a non-promtable JT
        wf_job = wfjt.launch(payload=dict(scm_branch='wfjt_prompt_branch')).wait_until_completed()
        assert wf_job.scm_branch == 'wfjt_prompt_branch'  # sanity
        wf_job.assert_status('failed')  # Should fail because branch does not exist
        wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
        job = wf_job_node.related.job.get()
        assert job.scm_branch == 'fake_branch'

    @pytest.mark.parametrize('refspec, good_ref, bad_ref', [
        ('+refs/pull/62/head:refs/remotes/origin/pull/62/head', 'pull/62/head', 'pull/hotdog/catsup'),
        ('+refs/pull/62/head:pull/hotdog/catsup', 'pull/hotdog/catsup', 'pull/62/head'),
        ('+refs/pull/*/merge:refs/pr/merges/*', 'pr/merges/94', 'pull/94/head')
        ],
        ids=[
            '+refs/pull/62/head:refs/remotes/origin/pull/62/head',
            '+refs/pull/62/head:pull/hotdog/catsup',
            '+refs/pull/*/merge:refs/pr/merges/*'
            ]
        )
    def test_scm_refspec_for_github_pr(self, v2, factories, refspec, good_ref, bad_ref):
        # TODO: Discuss more scenarios/valid syntax we want coverage for with @AlanCoding
        host = factories.host()
        inventory = host.related.inventory.get()

        project = factories.project(
            allow_override=True,
            scm_type='git',
            scm_refspec=refspec
            )

        jt = factories.job_template(
            project=project,
            inventory=inventory,
            ask_scm_branch_on_launch=True,
            allow_simultaneous=True
        )

        job_succeed = jt.launch(dict(scm_branch=good_ref))
        job_fail = jt.launch(dict(scm_branch=bad_ref)).wait_until_completed()
        job_succeed = job_succeed.wait_until_completed()
        job_fail.assert_status(['error', 'failed'])
        job_fail.related.project_update.get().assert_text_in_stdout("did not match any file(s) known to git")
        job_succeed.assert_successful()

    @pytest.mark.parametrize('bad_scm_refspec, good_scm_refspec, scm_branch', [
        ('+refs/pull/9:whatever', '+refs/pull/62/head:whatever', 'whatever'),
        ('+refs/pull/9:refs/remotes/origin/pull/9', '+refs/pull/62/head:refs/remotes/origin/pull/62/head', 'pull/62/head'),
        ])
    def test_update_project_scm_refspec(self, v2, factories, bad_scm_refspec, good_scm_refspec, scm_branch):
        host = factories.host()
        inventory = host.related.inventory.get()

        project = factories.project(
            allow_override=True,
            scm_type='git',
            scm_refspec=bad_scm_refspec
            )

        jt = factories.job_template(
            project=project,
            inventory=inventory,
            ask_scm_branch_on_launch=True,
            allow_simultaneous=True
        )

        job_fail = jt.launch(dict(scm_branch=scm_branch)).wait_until_completed()
        project.get().related.last_update.get().assert_text_in_stdout("Couldn\'t find remote ref")
        job_fail.assert_status(['error', 'failed'])
        assert "The project revision for this job template is unknown" in job_fail.job_explanation

        project.scm_refspec = good_scm_refspec
        job_succeed = jt.launch(dict(scm_branch=scm_branch)).wait_until_completed()
        job_succeed.assert_successful()

        # Now clear it out, it should use default branch and it should all still work
        project.scm_refspec = ''
        job_succeed = jt.launch().wait_until_completed()
        project.related.last_update.get().assert_successful()
        # If this fails then we cannot "undo" having run a job against a branch that needed the refspec
        # That has now been cleared out
        job_succeed.assert_successful()
