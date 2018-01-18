### Developer Resources

Here are additional resources in `tower-qa` and `towerkit` that may be helpful to other Ansible Tower engineering teams members.
* Use our tests to see how the Tower API is supposed to work. For instance, how to create an [Insights inventory](https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py#L20) or how Tower is supposed to behave interacting with Insights under [various scenarios](https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py#L78) (see "test_access_insights_with" tests).
* Credentials for the [majority](https://github.com/ansible/tower-qa/blob/master/config/credentials.vault) of our cloud integrations and additional authentication services.
* Schema files [documentating](https://github.com/ansible/towerkit/tree/master/towerkit/api/schema) expected API JSON.
* Using Towerkit to instantiate [resources](https://github.com/ansible/tower-qa/blob/master/scripts/resource_loading/load_tower.py).
* If you are feeling lazy, you can do this with tests:
```
    def test_fake(self, authtoken, factories):
        for _ in range(10):
            factories.v2_organization()
        import pdb; pdb.set_trace()
```
* Using Towerkit to validate that resources are properly displayed in the tower UI by changing name generation [tunables](https://github.com/ansible/towerkit/blob/master/towerkit/utils.py#L243).  
