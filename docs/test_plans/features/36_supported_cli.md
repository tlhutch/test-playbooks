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

- [ ] If insufficient arguments are provided to the CLI return help text.
- [ ] Catalog the required args for each creatable object and verify it is
      indicated as required in the help text

### Basic API interaction

- [x] Verify can launch a job from a JT
- [x] Verify can launch a project update
- [ ] Verify can check on a job status given we know a job ID
- [ ] Verify that booleans are cast correctly and handle reasonable input (case insensitive and cast 0 and 1 to false and true)
- [ ] Verify that `inventory_scripts` and `extra_vars` text can come from subshell output


### Custom CLI Features

- [ ] Verify we can move data from one tower to another with send/receive feature
  - could consider trying to re-use some of the upgrade testing
  - could consider adding a new job on release verification pipeline? Consult @Spredzy about this
- [ ] Verify that the following can trail STDOUT from a launchable resource with `--monitor`
  - Project update on create
  - [x] Project update
  - [x] Job launch
  - [x] inventory update
  - [x] ad hoc command
  - [x] workflow job templates
- [ ] Verify that the following can wait for job completion from a launchable resource with `--wait`
  - Project update on create
  - [ ] Project update
  - [x] Job launch
  - [ ] inventory update
  - [ ] ad hoc command
  - [ ] workflow job templates

- [x] Confirm can request output in human readable format and comes out as a table
- [x] Manually confirm that human readable output provided by tabulate looks good and is sane. Intentionally not going to automate this other than ability to call it.
- [x] Confirm can use jq to filter output
- [x] Confirm can request yaml output


### API Verification Criteria

### Packaging verification criteria

- [ ] awxkit has same version as awx
- [ ] ansible-tower-cli will have same version as tower: related https://github.com/ansible/awx/pull/4459
- [ ] ansible-tower-cli has RPM built for rhel7
- [ ] ansible-tower-cli has RPM built for rhel8
- [ ] confirm that job that tests rhel8 uses a rhel8 test-runner such that we can verify the CLI runs on python3 when it is the system python. Consult @Spredzy about this
- [ ] confirm that job that tests rhel7.6 uses a rhel7.6 test-runner such that we can verify the CLI runs on python2 when it is the system python. Consult @Spredzy about this
- [ ] confirm that job that tests rhel7.7 uses a rhel7.7 test-runner such that we can verify the CLI runs on python3 when it is the system python. Consult @Spredzy about this
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
- [ ] Have examples of using subshells to provide text for free entry args
      (`inventory_scripts`, `extra_vars`)
- [ ] Verify that required arguments are indicated as such in the help text,
      should not be in square brackets, see `job_templates` arguments `project` and
      `playbook`

## Open questions

- Do we care that extra arguments are ignored silently?
  - This is probably an API issue as the CLI doesn't know what arguments are
    valid.
  - Why was `scm_type` and `organization` not required to make a project
- Why is ad_hoc_commands only plural
- Want to clarify that creating a ad_hoc command launches it???????
- Should we be able to modify an ad_hoc command if it cant be re-launched? (no apparent way to do this)
- relaunch? does not seem to be implemented
- Way to sort by required/optional args for help text?
- Can human output for metrics endpoint get output in text/plain instead of weird empty list?
- Help text documents we cannot filter json or yaml outputs, caleb wants to know why
- way to help dumb users figure out when need --id and when is bare argument (smart users might notice that list takes --id but modify, launch, delete, and get take an action on a specifc one that they take as a positional argument)
