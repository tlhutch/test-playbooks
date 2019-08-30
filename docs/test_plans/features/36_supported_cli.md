# Supported CLI shipped with Tower 
## Owner

Primary: Elijah DeLee (@kdelee)
Secondary: Caleb (@squidboylan)

## Summary

Provide a supported CLI that offers feature parity with previously upstream [tower-cli](https://github.com/ansible/tower-cli).

## Related Information

- [tower ticket](https://github.com/ansible/tower/issues/2785)
- [test ticket](https://github.com/ansible/tower-qa/issues/3400)
- [opensourcing towerkit -> awxkit](https://github.com/ansible/towerkit/issues/571)
- [initial awx PR](https://github.com/ansible/awx/pull/4451)
- [initial tower-qa cli tests](https://github.com/ansible/tower-qa/pull/3937)
- [old 3.5.x docs for tower-cli](https://docs.ansible.com/ansible-tower/latest/html/towerapi/tower_cli.html)

## Verification Criteria

### Basic CLI functionality

- [x] If insufficient arguments are provided to the CLI return help text.
- [x] Catalog the required args for each creatable object and verify it is
      indicated as required in the help text
      - [x]  `awx login --help` should indicate that conf.username and conf.password
      - [x]  `awx users create --help` should indicate ['username', 'password']
      - [x]  `awx organizations create --help` should indicate ['name']
      - [x]  `awx projects create --help` should indicate ['name']
      - [x]  `awx teams create --help` should indicate ['name', 'organization']
      - [x]  `awx credentials create --help` should indicate ['name', 'credential_type', choice(['user', 'team', 'organization'])]
      - [x]  `awx credential_types create --help` should indicate ['name', 'kind']
      - [x]  `awx applications create --help` should indicate ['name', 'client_type', 'authorization_grant_type', 'organization']
      - [x]  `awx tokens create --help` should indicate no required args
      - [x]  `awx inventory create --help` should indicate ['name', 'organization']
      - [x]  `awx inventory_scripts create --help` should indicate ['name', 'organization', 'script']
      - [x]  `awx inventory_sources create --help` should indicate ['name', 'inventory']
      - [x]  `awx groups create --help` should indicate ['name', 'inventory']
      - [x]  `awx hosts create --help` should indicate ['name', 'inventory']
      - [x]  `awx job_templates create --help` should indicate ['name', 'playbook', 'project']
      - [x]  `awx ad_hoc_commands create --help` should indicate ['inventory', 'credential', 'module_args']
      - [x]  `awx schedules create --help` should indicate ['rrule', 'unified_job_template', 'name']
      - [x]  `awx notification_templates create --help` should indicate ['name', 'organization', 'notification_type']
      - [x]  `awx labels create --help` should indicate ['name', 'organization']
      - [x]  `awx workflow_job_templates create --help` should indicate ['name']
      - [x]  `awx workflow_job_template_nodes create --help` should indicate ['workflow_job_template', 'unified_job_template'] MAY CHANGE when WORKFLOW APPROVAL NODE merges
- [ ] verify that all commands have aliases that conform to old CLI (download old CLI and run --help)

### Basic API interaction

- [x] Verify can launch a job from a JT
- [x] Verify can launch a project update
- [ ] Verify can check on a job status given we know a job ID
- [x] Verify that booleans are cast correctly and handle reasonable input (case insensitive and cast 0 and 1 to false and true)
- [ ] Verify that `inventory_scripts` and `extra_vars` text can come from subshell output e.g. `--extra_vars=$(cat extra_vars.yaml)`
   - [ ] Need to investigate what tower-cli does
- [ ] Verify that we do not have a `ad_hoc_commands modify`


### Custom CLI Features

- [ ] Verify we can move data from one tower to another with send/receive feature
  - could consider trying to re-use some of the upgrade testing
  - could consider adding a new job on release verification pipeline? Consult @Spredzy about this
- [x] Verify that the following can trail STDOUT from a launchable resource with `--monitor`
  - [x] Project update on create
  - [x] Project update
  - [x] Job launch
  - [x] inventory update
  - [x] ad hoc command
  - [x] workflow job templates
- [ ] Verify that the following can wait for job completion from a launchable resource with `--wait`
  - [ ] Project update on create
  - [ ] Project update
  - [x] Job launch
  - [ ] inventory update
  - [ ] ad hoc command
  - [ ] workflow job templates

- [x] Confirm can request output in human readable format and comes out as a table
- [x] Manually confirm that human readable output provided by tabulate looks good and is sane. Intentionally not going to automate this other than ability to call it.
- [x] Confirm can use jq to filter output
- [x] Confirm can request yaml output
- [ ] associate + dissociate notifications to
   - [ ] job templates
   - [ ] projects
   - [ ] inventory updates
   - [ ] organizations
   - [ ] workflow job templates
- [ ] associate + dissociate credentials to
   - [ ] job templates
- [x] JSON/YAML input for credential type inputs
- [ ] Ensure that providing a private ssh key is a seamless and well documented experience. Should not require 12 fingers
- [ ] Validate that users can be associated with an organization
- [x] Validate that users can be granted roles to organization, project, inventory, inventory_script, team, credential, job_template, and workflow_job_template
- [x] Validate that users can have roles revoked to organization, project, inventory, inventory_script, team, credential, job_template, and workflow_job_template


### Pain points to check
- [x] hide `--id` on `list` so users dont get confused
- [x] for things like `--project` or `--inventory` etc we need to show in the help text `PROJECT ID` not `PROJECT` because what does that mean anyway

### Packaging verification criteria

- [x] awxkit has same version as awx (is symlink to awx version)
- [ ] awxkit tarball will be release artifact on awx github
- [ ] ansible-tower-cli will have same version as tower: related https://github.com/ansible/awx/pull/4459
- [x] ansible-tower-cli has RPM built for rhel7
- [x] ansible-tower-cli has RPM built for rhel8
- [x] confirm that job that tests rhel8 uses a rhel8 test-runner such that we can verify the CLI runs on python3 when it is the system python.
- [x] confirm that job that tests rhel7.7 uses a rhel7.7 test-runner such that we can verify the CLI runs on python2 when it is the system python.
- [x] confirm that tests delete the `awx` binary available in the tower-qa venv
- [x] confirm that tests are configurable to call the `ansible-tower-cli` or `awx`  binary available in PATH
- [x] confirm that we install the rpm for the `ansible-tower-cli` from the right repo
- [ ] Confirm we resolve the dependency issue
- [ ] anisble-tower-cli has source tarball built for pip install on other distro (hosted at ansible.releases.com)


## Docs Verification Criteria

- [ ] Verify the CLI docs don't have any rendering issues
 - [ ] This would be a good candidate for zuul check in future, maybe need RFE for this
- [ ] Verify that the docs for passing related objects
      indicate what the data should be (id, name, etc)
- [ ] Verify that things like `extra_vars` has an example or clear instruction
      of how to pass data to it (object like string? Dict? etc)
- [ ] Help text and error message should indicate if an ID is expected rather
      than a name
- [ ] Have examples of using files to provide text for free entry args
      (`inventory_scripts`, `extra_vars`)

## Answered questions

- Do we care that extra arguments are ignored silently?
  - This is probably an API issue as the CLI doesn't know what arguments are
    valid.
  - Stuck with this
- Why was `scm_type` and `organization` not required to make a project
  - just the way the api works
- removed tabulate dependency
- jq will remain optional dependency that is left as exercise for the reader to install because we don't want to build it


# candidates for RFE's
- Relaunch implementation across board
- Sort by required/optional args for help text in initial list of args
- Add support for filtering yaml
- Sane interface for providing launch time parameters (prompt on launch)
- Add support for callback endpoint for job_templates so the hosts can reach back and launch job templates
- _DONOTFILE_ draw crazy workflow graph on command line
- _DONOTFILE_ export/import workflow graphs via yaml
- Support totally wiping your tower install instead of truncating database

## Open questions
  - how is one supposed to interact with instance groups, not sure how I am supposed to acheive modifying instances associated. This is probably part of general "How to deal with related items" problem
