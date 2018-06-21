### Writing Tests

This document is about writing integration tests in `tower-qa`. Before we dive in, there are a few things that I will point out so that you can get a lay of the land.

First, we use `factories` to instantiate Tower resources. [Here](https://github.com/ansible/tower-qa/blob/master/tests/lib/fixtures/factory_fixtures.py#L230) are the resources that you can create.
* You can use kwargs to update the payload sent for resource instantiation. You can see which kwargs we support by looking at the `create` and `payload` methods under each of our page objects. For an example of this, see [here](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/job_templates.py#L104).
* For an example of resource instantiation using factories, see [here](https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py#L99).
* When you create resources with `factories`, we will [delete](https://github.com/ansible/tower-qa/blob/master/tests/lib/fixtures/factory_fixtures.py#L27) them upon test completion. We do this to prevent tests from interfering with other tests.

More about our page objects:
* Our page objects map to specific API endpoints and we manually register a selection of API endpoints with these page objects. You can see an example of page registration [here](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/inventory.py#L344). We register each of our page objects.
* The master API resource list that we use is [here](https://github.com/ansible/towerkit/blob/master/towerkit/api/resources.py). When we add new endpoints to the API, we have to update this list.
* Our page objects help us because they have an assortment of helper methods. The idea is to abstract out as many repeatable chunks of code into helper methods as possible.
* For instance, one thing that we do all of the time in our tests is to launch a job template. Instead of submitting a POST to `/api/v2/job_templates/N/launch/` over and over, we simply call the following handy [helper method](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/job_templates.py#L41):
```
jt.launch()
```
* Our page object helper methods are one of the huge advantages that Towerkit brings.

About dependency stores:
* Most of our page objects have dependency stores, which are an easy way to access resource dependencies.
* What we mean by "dependency" is this: to create a team resource in Tower, you need an organization. So organizations are dependencies of teams to us.
* You can access the dependency store and its resources as follows:
```
>>> job_template.ds
['project', 'credential', 'inventory']
>>> credential = job_template.ds.credential
>>> credential.endpoint
u'/api/v2/credentials/137/'
```

Next about schema validation:
* Everytime we make a REST request to the API, we [validate](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/page.py#L149) the JSON structure that the API returns to us.
* We do this to ensure that we have a stable API: changes in API JSON output should be intentional. One of the main reasons why our customers buy Tower is because of our API and we want to respect customer integrations with the Tower backend.
* We keep static [Python files](https://github.com/ansible/towerkit/blob/master/towerkit/api/schema/v1/ping.py) that serve as the source of truth when validating schema. In other words, if API JSON differs from these Python schema files, we will raise a schema validation error if schema validation is enabled.
* As of June 20th, 2018, we only enable schema validation on our Oracle Linux standalone Tower integration runs.
* You may turn schema validation off [here](https://github.com/ansible/towerkit/blob/master/towerkit/config.py#L29).

Tips for writing good tests:
* Be iterative. Write a chunk of code, then throw in `pdb` break, inspect output to ensure code quality, and move on.
```
        job_template_with_extra_vars.ask_variables_on_launch = True
        job_template_with_extra_vars.add_survey(spec=required_survey_spec)

        import pdb; pdb.set_trace()  # pdb is your friend
```
* We try to have descriptive test names. In other words, your test name should fully encapsulate what we are trying to test. Examples of good test names include:
  - `test_tower_web_service_should_be_able_to_recover_from_zero_tower_pods`
  - `test_verify_jobs_fail_with_execution_node_death`
  - `test_jt_with_no_instance_groups_defaults_to_tower_instance_group_instance`
* Fixtures belong in test [classes](https://github.com/ansible/tower-qa/blob/master/tests/api/cluster/test_execution_node_assignment.py#L33) _if_ you don't see them ever being used for tests outside of the class. We do this to preserve the global fixtures namespace.
* If you forsee tests outside of a specific class needing a fixture, add it to `tests.lib.fixtures.api`.
* If you are trying to assert that Tower is raising a specific error message, use this [construction](https://github.com/ansible/tower-qa/blob/master/tests/api/credentials/test_credentials.py#L193).
* We have a library of helpful utilities [here](https://github.com/ansible/towerkit/blob/master/towerkit/utils.py#L185). For instance, we have utilities for job polling here. Before creating your own, consider whether your utility belongs in Towerkit.
* We adhere to PEP8. Please run `flake8` locally before submitting a PR to `tower-qa` or `towerkit`.

Learn by imitation. Examples of great tests and test writing include:
* https://github.com/ansible/tower-qa/blob/master/tests/api/test_insights.py
* https://github.com/ansible/tower-qa/blob/master/tests/api/schedules/test_schedules.py
* https://github.com/ansible/tower-qa/blob/master/tests/api/test_fact_cache.py

We appreciate your contributions to `tower-qa`! We can achieve great things together.

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) June 21, 2018.
