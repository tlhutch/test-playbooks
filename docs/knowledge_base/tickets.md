### Writing Tickets

One of the things that you will do a lot here is writing tickets for our development team. Steps to write a good ticket include:
* Very clear steps to reproduce (someone new to the team should be able to follow your directions).
* Clear expected results and actual results.
* Screenshots / gifs are useful. I use [licecap](https://www.cockos.com/licecap/); there are other tools available.

Tickets should have associated labels.
* All new tickets should have `needs_devel` and an associated milestone (which release should include our fix)?
* Each ticket should have a priority label. We use these guidelines:
    - High priority means this is something that must be addressed and soon. We generally use the high priority label when core Tower functionality is broken or other team members are blocked.
    - Medium priority means that this is something that needs get addressed before we release.
    - Low priority means that this is something that we neeed, but we can safely release without an associated fix. A certain percentage of the time, low priority issues will never get addressed.
* Each ticket should have a `component` label. These include `ui`, `api`, and `installer` for instance.
* Each ticket needs a `type` label. These include `bug` and `enhacenement`.

Sometimes we should include environment information. This includes:
* Version of Tower (`version` flag under `/api/v2/ping/`).
* Tower installation method (standalone, cluster, OpenShift).
* Linux platform (Centos, Ubuntu).
* Ansible version.

Here is a great example of a [UI ticket](https://github.com/ansible/tower/issues/1214). For a great example of an API ticket, see [here](https://github.com/ansible/tower/issues/1418).

### Verifying Tickets

There are two ways in which we can verify a ticket: through manual testing and through writing an automated test. We use the following criteria in deciding whether to write an automated test for something:
* In general, we like to write as many automated tests as possible. You can think about things this way: if we manually test, we verify functionality at a specific point in time; if we write an automated test, we _theoretically_ verify functionality forever.
* Practically, however, not all issues needs to get an automated test. Think about:
    - Is what we're testing important to the Tower user? If it is, we should write a test. If it's something super granular or a cornercase, let's manually test instead.
    - Is this something that is likely to change often? If it is, let's not write a test until functionality settles unless we're prepared for churn.
    - Is this something that we already have tests for? The tests under `tests.api` generally map to API endpoints; for             instance, `tests.api.me` maps to the `/api/v2/me/` endpoint.
    - Do we already have unit or functional tests for this? Generally speaking, we should [favor](https://martinfowler.com/bliki/TestPyramid.html) unit and functional tests over tower-qa integration tests.
    - How much time do we have? If it is going to take a lot of time to write an automated test for something and we are running close to our deadlines, consider manual verification.

How to manually test something:
* Assign yourself the ticket and replace the `state:needs_test` label with the `state:test_in_progress` label when you begin testing.
* Write a section detailing the steps that you used to test. Someone should be able to come in and reproduce your flow by reading the instructions that you leave here. This is important since sometimes, we will have to revisit tickets later (let's say a defect is found). In instances like this, it is important to know what work we've already done.
* Include in your test writeup the Tower version with which you've tested against.
* Close the ticket when you're done.
* If you find a problem with the fix or improvement, unassign yourself from the ticket, remove the "Testing in Progress" label, and assign the "Needs Devel" label to the ticket.
* Here is a good example of a [this](https://github.com/ansible/ansible-tower/issues/5939#issuecomment-293631632).

For instructions on writing an automated test, see [here]() (TBD).

Written by [Christopher Wang](mailto:chrwang@redhat.com) (Github: simfarm) June 20, 2018.
