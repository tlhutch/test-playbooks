# Subscription and Enforcement License Changes
## Owner

Primary: Caleb (@squidboylan)
Secondary: Elijah DeLee (@kdelee)

## Summary

For legal purposes, we must *not* terminate usage/restrict functionality after:
     - the license ends
     - the number of managed nodes provided by the license is exceeded
Provide a new _optional_ interaction in the UI _at license application time_ which allows you to specify Red Hat a Red Hat subscription username and password **instead of** uploading a license key file.

## Related Information

- [tower ticket](https://github.com/ansible/tower/issues/3550)
- test ticket TBD
- [initial awx PR](https://github.com/ansible/awx/pull/4611)
- [initial tower-license PR](https://github.com/ansible/tower-license/pull/10/)

## Verification Criteria

### License Generation
- [ ] On the license application screen, users may *optionally* specify a username and password in lieu of a license file
    - [ ] If invalid credentials are provided, a meaningful error message is printed in the Tower logs
    - [ ] If the license server is unreachable, a meaningful error message is printed in the Tower logs
- [ ] Tower license data generated via Red Hat's subscription APIs meets the following requirements:
    - [ ] If there is *no* active Tower subscription (one of several predefined SKUs), a license is not generated
    - [ ] If there is exactly *one* active Tower subscription, a license is generated which:
      - has a subscription name that matches the RH product name (i.e., Ansible Tower by Red Hat, Standard (100 Nodes))
      - has an expiration date that matches the *end* date of the RH subscription
      - has a total node count that is correct (based on the SKU and quantity provided by the Red Hat API)
    -  [] If there are **multiple** active Tower subscriptions, we will generate a license based on the details of the subscription that ends **soonest**.

### Enforcement
- If a *trial* license is provided:
  - [ ] the API prevents you from creating hosts *past* your managed node count.  This includes:
    - [ ] manually creating hosts via the API
    - [ ] importing inventory via an inventory source
  - [ ] the API drastically limits functionality when your license becomes expired
- If a *non*-trial is provided (included via the new RH login mechanism)
  - [ ] the API **allows** you to create hosts *past* your managed node count, but warns you (loudly) in the Tower logs when you do so
  - [ ] the API does *not* limit functionality in any way when your license becomes expired
