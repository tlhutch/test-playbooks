# How to test compatibility with Ansible

## Overview

The challenge:

* Ansible Core does not guarantee a stable interface
* Because Tower invokes Ansible, it implicitly makes certain assumptions about Ansible's interface
* Changes to Ansible can break existing tower releases, as well as releases under development

The QE team has two sets of tests in Jenkins that help to ensure that Ansible remains compatible with Tower:

### Integration tests for the version of Tower under development

QE's integration tests test the _version of Tower under development_ against each supported version of Ansible. There are two sets of integration tests:

Those that focus on major and minor releases:

* [Test_Tower_Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration/) - tests standalone Tower
* [Test_Tower_Integration_Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Cluster/) - tests the traditional Tower cluster

.. and those that focus on patch releases:

* [Test_Tower_Integration_Patch](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration_Patch/) - tests standalone Tower
* [Test_Tower_Cluster_Patch](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Cluster_Patch/) - tests the traditional Tower cluster
* [Test_Tower_Integration_Patch_3.1.x](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration_Patch_3.1.x/) - tests standalone Tower for 3.1.x patch releases, specifically

The [Test_Tower_Upgrade](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Upgrade/) test also runs against every supported version of Ansible.

### Compatibility tests for the latest Tower release

The [Ansible Core / Tower Compatibility Test](http://jenkins.ansible.eng.rdu2.redhat.com/job/Ansible_Tower_Integration_Test/#) tests the _latest release of Tower_ against each supported version of Ansible.

## Providing Core with instructions for running the compatibility test

The Ansible Core team maintains a block of instructions on how to kick off and review the results for the compatibility test. Those instructions can be found in a release engineering document located [here](https://github.com/ansible/community/wiki/RelEng:-ReleaseProcess#release-procedure).

If this document is out-of-date, contact a member of the core team in #testing, and offer to edit the wiki page's instructions so that it's current. The wiki page can be edited in place.

After making changes, click on the `X Revisions` link (just underneath the title of the page at top), select your change and the change immediately preceding that, and click Compare Revisions. Copy the link to the following page showing the changes and paste it in #testing so members of the core team can see / review the changes.

## Updating Jenkins jobs to include new Ansible releases

When the Ansible team creates a new `stable-*` branch, use the following checklist to ensure that all jobs are updated to include the new branch:

* Update [Stable_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/job/Stable_Ansible/configure)'s `GIT_REFSPEC` and `GIT_TESTED_BRANCHES` parameters to include the new branch.
* Update [Test_Tower_Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install/configure) and [Test_Tower_Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration/configure)'s `ANSIBLE_NIGHTLY_BRANCH` list to include the new branch.
* Update [Test_Tower_Install_Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install_Cluster/configure) and [Test_Tower_Integration_Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration_Cluster/configure)'s `ANSIBLE_NIGHTLY_BRANCH` list to include the new branch.
* Update [Test_Tower_Integration_Patch](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Patch/configure)'s `ANSIBLE_NIGHTLY_BRANCH` parameter to include the new branch.
* Update [Ansible_Tower_Integration_Install](http://jenkins.ansible.eng.rdu2.redhat.com/job/Ansible_Tower_Integration_Install/configure) and [Ansible_Tower_Integration_Test](http://jenkins.ansible.eng.rdu2.redhat.com/job/Ansible_Tower_Integration_Test/configure)'s `ANSIBLE_NIGHTLY_BRANCH` list to include the new branch.
* Update [Test_Tower_Upgrade](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Upgrade/configure)'s `ANSIBLE_BRANCH` parameter to include the new branch.
* Update [Ansible Version Bump](http://jenkins.ansible.eng.rdu2.redhat.com/job/Ansible%20Version%20Bump/configure)'s `GIT_REFSPEC` parameter to include the new branch.

Note: When upgrading patch install / integration jobs, especially versions that are pinned to specific, older releases (e.g. [Test_Tower_Integration_Patch_3.1.x](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Patch_3.1.x/)), make sure that the versions of tower that will be installed / tested using the job support the new version of Ansible. You can confirm this by checking [this knowledge base article](https://access.redhat.com/articles/3382771). Note that you must be logged in to access.redhat.com to see all of the information on the page.

## Alerting the team to new Ansible releases

The [Ansible Version Bump](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible%20Version%20Bump/) job monitors the `devel` and `stable-*` branches of Ansible, looking for changes in the [lib/ansible/release](https://github.com/ansible/ansible/blob/devel/lib/ansible/release.py) file. When it detects a change, it will post a message in the QE team's slack channel (`#ship_it`), alerting the team to the possibility of a release being staged. This job is intended to provide a safety net for vetting Ansible releases and is not intended as a substitute for communication between the Tower and Core teams. The monthly Core + Tower test sync-up meeting is one place where the two teams can touch base about upcoming releases.

# Reference
* The Tower and Core teams collaborate on testing in the `#testing` channel on Slack
* [Ansible Release Engineering Process](https://github.com/ansible/community/wiki/RelEng)
* [Core + Tower Test Sync-up - Running notes](https://docs.google.com/document/d/15XyyMT-tfQJwFnUXQpcwWRVSZQRpMrUirwuOnVxkiw4/edit#)
* [Matrix showing which versions of Ansible are supported for each version of Tower](https://access.redhat.com/articles/3382771) (Note: Must be logged in to access.redhat.com)

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Aug 31, 2018.
