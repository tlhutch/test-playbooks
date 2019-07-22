# Ansible-runner integration for tasks and isolated nodes

## Owner

Primary: Yanis
Secondary: Danny

## Summary

This test plan applies for two different stories:

  * Move Tower to ansible-runner for task execution
  * Using ansible-runner on isolated nodes


## Related Information

- [Tower Ticket: Task Execution](https://github.com/ansible/tower/issues/3031)
- [Tower Ticket: Isolated nodes](https://github.com/ansible/tower/issues/3251)
- [Ansible Runner](https://ansible-runner.readthedocs.io/en/latest/)


## Verification Criteria

- [ ] Build processes still work
- [ ] Install (bundle and non-bundle) + integration passes
- [ ] Upgrade (bundle and non-bundle) + integration passes


## Additional Information

Even though runner will allow to reduce the matrix from stable-2.6, stable-2.7,
devel to just one item, until the porting of tests are not done over `ansible/ansible-runner`
nothing should change on current QE front.
