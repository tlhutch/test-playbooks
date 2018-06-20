### Developer Resources

Here are additional resources in `tower-qa` and `towerkit` that may be helpful to other Ansible Tower engineering teams members.
* Use our tests to see how the Tower API is supposed to work. For instance, how to create an [Insights inventory](https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py#L20) or how Tower is supposed to behave interacting with Insights under [various scenarios](https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py#L78) (see "test_access_insights_with" tests).
* Credentials for the [majority](https://github.com/ansible/tower-qa/blob/master/config/credentials.vault) of our cloud integrations and additional authentication services.
* Schema files [documentating](https://github.com/ansible/towerkit/tree/master/towerkit/api/schema) expected API JSON.
* Using Towerkit to instantiate resources using `tkit`:
```
tkit -l -c config/credentials.yml -t http://127.0.0.1:8013

In [1]: for i in range(10): v2.teams.create()
DEBUG:towerkit.api.pages.page:Retrieved <class 'towerkit.api.pages.teams.V2Teams'> by url: /api/v2/teams/
DEBUG:urllib3.connectionpool:http://127.0.0.1:8013 "POST /api/v2/organizations/ HTTP/1.1" 201 2078
DEBUG:towerkit.api.client:"POST http://127.0.0.1:8013/api/v2/organizations/" elapsed: 0:00:00.163769
DEBUG:urllib3.connectionpool:http://127.0.0.1:8013 "POST /api/v2/teams/ HTTP/1.1" 201 1345
DEBUG:towerkit.api.client:"POST http://127.0.0.1:8013/api/v2/teams/" elapsed: 0:00:00.099482
...
...
```

* Using Towerkit to validate that resources are properly displayed in the tower UI by changing name generation [tunables](https://github.com/ansible/towerkit/blob/master/towerkit/utils.py#L243).
* Playbooks for installing Tower in various configurations. For instance, with [LDAP](https://github.com/ansible/tower-qa/blob/master/playbooks/deploy-tower-ldap.yml) or with [bundle installer](https://github.com/ansible/tower-qa/blob/master/playbooks/deploy-tower-bundle.yml).

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) Janury 25, 2018.
