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
* For instance, one thing that we do all of the time in our tests is to launch a job template. Instead of submitting a POST to `/api/v2/job_templates/N/launch/` over and over, we simply call the following because of our handy [helper method](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/job_templates.py#L41):
```
jt.launch()
```
* Our page object helper methods are one of the huge advantages that Towerkit brings.

Next about schema validation:
* Everytime we make a REST request to the API, we [validate](https://github.com/ansible/towerkit/blob/master/towerkit/api/pages/page.py#L149) the JSON structure that the API returns to us.
* We do this to ensure that we have a stable API: changes in API JSON output should be intentional. One of the main reasons why our customers buy Tower is because of our API and we want to respect customer integrations with the Tower backend.
* We keep static [Python files](https://github.com/ansible/towerkit/blob/master/towerkit/api/schema/v1/ping.py) that serve as the source of truth when validating schema.
* As of June 20th, 2018, we only enable schema validation on our Oracle Linux standalone Tower integration runs.
* You may turn schema validation off [here](https://github.com/ansible/towerkit/blob/master/towerkit/config.py#L29).

