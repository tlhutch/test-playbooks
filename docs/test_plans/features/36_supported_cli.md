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

- [ ] Verify can launch a job from a JT
- [ ] Verify can check on a job status given we know a job ID
- [ ] Verify can create and pass all valid kwargs we want:
  - [ ] organization
  - [ ] project
  - [ ] job template
  - [ ] workflow job template
  - [ ] workflow job template node
- [ ] Verify we can move data from one tower to another with send/receive feature
  - could consider trying to re-use some of the upgrade testing
  - could consider adding a new job on release verification pipeline? Consult @Spredzy about this



### API Verification Criteria

### Packaging verification criteria

- [ ] awxkit has same version as awx
- [ ] ansible-tower-cli will have same version as tower: related https://github.com/ansible/awx/pull/4459
- [ ] ansible-tower-cli has RPM built for rhel7
- [ ] ansible-tower-cli has RPM built for rhel8
- [ ] confirm that job that tests rhel8 uses a rhel8 test-runner such that we can verify the CLI runs on python3 when it is the system python. Consult @Spredzy about this
- [ ] anisble-tower-cli has source tarball built for pip install on other distro (hosted at ansible.releases.com)

### Docs Verification Criteria
