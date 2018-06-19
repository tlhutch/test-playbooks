### Writing Tickets

One of the things that you will do a lot here is writing tickets for our development team. Steps to write a good ticket include:
* Very clear steps to reproduce (someone new to the team should be able to follow your directions).
* Clear expected results and actual results.
* Screenshots / gifs are useful. I use [licecap](https://www.cockos.com/licecap/); there are other tools available.

Sometimes we should include environment information. This includes:
* Version of Tower (`version` flag under `/api/v2/ping/`.
* Tower installation method (standalone, cluster, OpenShift).
* Linux platform (Centos, Ubuntu).
* Ansible version.

Here is a great example of a [UI ticket](https://github.com/ansible/tower/issues/1214). For a great example of an API ticket, see [here](https://github.com/ansible/tower/issues/1418).

### Verifying Tickets

To verify a ticket:
* Assign yourself the ticket and move it into the "Testing in Progress" column when you begin testing.
* Write a section detailing the steps that you used to test. Someone should be able to come in and reproduce your flow by reading the instructions that you leave here.
* This is important since sometimes, we will have to revisit tickets later (let's say a defect is found). In instances like this, it is important to know what work we've already done.
* Include in your test writeup the Tower version with which you've tested against.
* Close the ticket when you're done.
* If you find a problem with the fix or improvement, unassign yourself from the ticket, remove the "Testing in Progress" label, and assign the "Needs Devel" label to the ticket.

Here is a good example of a [this](https://github.com/ansible/ansible-tower/issues/5939#issuecomment-293631632).
