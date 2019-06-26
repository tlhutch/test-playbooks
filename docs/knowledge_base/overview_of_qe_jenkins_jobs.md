# Overview of QE Jenkins Jobs

We use Jenkins to manage the running of our automated tests.
[http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/#)

Note that in order to access the above link you will need to be on the Red Hat VPN.

The QE team as a whole maintains the pipelines and jobs listed below. Seasonally, the team will use a weekly rotation to review test results, write up regressions, and repair issues with the tests themselves. At all times it is an advisable and appropriate way to start your day by reviewing results of the pipelines at our dashboard located at http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/releases (you must be on RH network/VPN to see this).

## Release Verification Pipelines
The major release we are working on is always the top tab of http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/releases

For each OS/Ansible combination we support, there is a status "orb" that indicates the status of the latest pipeline run. Yellow means there were some failed tests, but otherwise builds and upgrades and such completed. Red means there was a job that completely failed or no test results found, green means GREEN!

By clicking on the status orb you will be directed to a jenkins blue ocean view of the pipeline that you can click through to find status for standalone integration, cluster integration, etc, etc.

Not every permutation runs the full test suite. Check in with the team for what permutations we run the full suite on nightly.

For minor releases, we run the upcoming minor release pipeline on a weekly basis, as well as more frequently as needed as we near release time.

## Self-Service Jobs + Pipelines

[Test_Tower_Yolo_Express](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Test_Tower_Yolo_Express/activity/) is your main point of contact if you want to deploy tower instances with specific branches and forks.

As a QE team member, `pipeline/Release`(http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Frelease-pipeline/activity) has replaced `Nightly_Tower`, which is now deactivated. It is a Jenkins pipeline that, based on the version specified, will trigger the proper actions. A Knowledge Base page is coming up to explain all the new pipelines available.

As a user, if all one wants is to install is a specific version of Tower,

`pipeline/Install`(http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Finstall-pipeline/activity) is here just for that.


## Ansible Core / Ansible Tower Product Integration Tests

Installs the latest release of Tower against Ansible development branches. Runs a subset of full integration that exercises the contact points between Tower and Ansible. Used by Tower team to sign-off on Ansible releases. A subset of the install / test jobs are triggered each night based on which development branches were changed in the past day.

- Ansible build jobs (maintained by Ansible Core team)
	- [Stable_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Stable_Ansible/) / [Nightly_Ansible](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Nightly_Ansible/) - trigger downstream build / install / test jobs
	- [Build_Ansible_TAR](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_TAR/)
	- [Build_Ansible_Public_RPM](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_Public_RPM/)
	- [Build_Ansible_DEB](http://jenkins.ansible.eng.rdu2.redhat.com/view/Ansible/job/Build_Ansible_DEB/)
- [Ansible_Tower_Integration_Install](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Install/)
- [Ansible_Tower_Integration_Test](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Ansible_Tower_Integration_Test/)

## UI Test Pipeline

[Test_Tower_E2E_Pipeline](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E_Pipeline/) - Runs the e2e ui tests

- Trigger: checks for scm changes against tower/release_X every 2 hours.
- Build: Builds RPM
- Deploy: Uses the Ansible Tower Jenkins plugin to deploy a RPM build to GCE
- Test: Runs the Test_Tower_E2E job against the GCE build
- Notify: Sends a slack notification to #e2e-resuts and notifies of failure or return-to-success in #ui-talk
[Test_Tower_E2E](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_E2E/) - General E2E test execution utility job. Requires a FQDN, username, password
Used as a part of the Test_Tower_E2E_Pipeline
Used after the Openshift Integration runs
Soon: Used post-upgrade pipeline

Written by [Jim Ladd](mailto:jladd@redhat.com) (Github: jladdjr) Oct 15, 2018.

## FAQ

* _When is the last time we were testing Tower version X.Y.Z with Ansible version X.Y.Z on OS X version Z and what were the results_
    * This is actually difficult to do! Jenkins only stores test results for 30 days.
    * Remediation: Archive results for each release and link to them from the release plan.
* _If I want to trigger a test of Tower version X.Y.Z with Ansible Version X.Y.Z on OS X version Z, how do I do that?_
    * Use the [YOLO](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Yolo_Express/) job if you require a feature branch

* _ We don't run full integration on all Ansible versions, right?_
    * No, Full integration is run with latest ansible version on each OS. So, right now, ansible stable-2.7 on each OS ( a whole column of matrix ).
    * The rest run `-m yolo or ansible_integration`. The `yolo` mark is a mark we have attempted to apply to get a minimum coverage of each component in Tower. the `ansible_integration` mark as been applied to tests known to expose our sensitive points of contact with breaking changes in Ansible.

* _How do you find results?_
    * Look a the dashboard to find latest results for OS/Ansible version of interest.

* _How do I tell how many times a test has failed in the nightly runs?_
    * The # in the test results is calculated based on job #’s  -- can be misleading
      Example: will say “failing for 25 builds” but actually it is only last night and tonight
      Because other jobs happened in between, incrementing the job #’s, but these were not runs from the nightly pipeline
      For a more accurate view, look at the particular test and then inspect the history (button on left when in detail view)
* _How can I inspect the health of a current feature in the test results?_
    * Expand “all test results” and click through the tree. Tests are organized by module and/or folder, each associated with a feature or function.
