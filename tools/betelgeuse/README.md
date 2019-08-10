Betelgeuse and Polarion Integration
===================================

The next sections explains and demonstrates how to import requirements, test
cases and test runs into Polarion. For running the commands demonstrated on the
sections below, make sure that some environment variables are set such as the
`POLARION_USERNAME` and `POLARION_PASSWORD`. Those environment variables are
required to proper login and access the Polarion importers.

Each project in Polarion usually have a machine user which is suited to be used
to import things into it. For the `Ansible Tower` project there is the
`ansible_machine` user. To use its credentials, run the commands below:

```console
$ export POLARION_USERNAME='ansible_machine'
$ export POLARION_PASSWORD='polarion'
```

Those are the minimum environment variables required to import requirements,
test cases and test runs into Polarion. By default if the `POLARION_URL` is not
specified then the scripts used to import will default to the stage Polarion
URL. That said, to target the production Polarion, run the following command:

```console
$ export POLARION_URL="https://polarion.engineering.redhat.com"
```


Importing requirements
----------------------

There is not an easy way to create the `requirements.xml` from the tower-qa
tests source. Because of that we need to maintain that manually. We have the
`requirements.xml` file availble on `tools/betelgeuse/requirements.xml`.

To import the requirements, run the following command from the root of the
tower-qa repo:

```console
$ ./tools/betelgeuse/scripts/polarion-import requirement tools/betelgeuse/requirements.xml
```

This should be done before importing test cases so that when the test cases are
imported they will be properly linked to the requirements. The following rules
are used to define a requirement for a given test case:

* Requirement will be `CLI` for any test under `tests/cli` directory.
* Requirement will be `License` for any test under `tests/license` directory.
* Requirement will be `Upgrade` for any test under `tests/upgrade` directory.
* For any test under `tests/api` the requirement will be built based on the
  test module name if it is a child of `tests/api` or directory under
  `tests/api` for any test that is in a subdirectory of `tests/api`. Check the
  `get_requirement_value` function on `tools/betelgeuse/betelgeuse_config.py`
  for more details.


Collecting and importing tests cases
------------------------------------

To collect the test cases and generate an XML file that is in the format to be
imported by the Polarion test-case importer run the following command from the
root of the tower-qa repo:

```console
$ ./tools/betelgeuse/scripts/gen-test-cases
```

The previous command will generate a `test-cases.xml` file on the
`reports/betelgeuse/` directory. Now test cases can be imported into Polarion
by running:

```console
$ ./tools/betelgeuse/scripts/polarion-import testcase reports/betelgeuse/test-cases.xml
```

A import job will be created and it will import new test cases or update test
cases that were already imported. The output of the above command will provide
a link to the import queue and the expected import logs when the import job is
completed.


Importing test results from a jUnit XML report
----------------------------------------------

tower-qa automation pipelines may generate multiple jUnit XML reports. If multiple files are generated then them can be merged together or the next steps should be run for each jUnit XML report. To merge the jUnit XML files run the following command from the root of the tower-qa repo:


```console
$ ./scripts/merge_junit junit-report1.xml junit-report2.xml junit-reportN.xml merged-report.xml
```

Next, we need to work around a [pytest-xdist bug](https://github.com/pytest-dev/pytest-xdist/issues/445). At the moment of this writing the bug is closed but it wasn't released yet. That said, run the following command to update the classname:

```console
$ ./scripts/update_junit_classname junit-report.xml junit-report-updated.xml
```

The above script does it best to work around the pytest-xdist bug it is not
100% effective since a test module with the same name as another can live on
multiple test directories. Currently the only conflict is test_base.py which
present on `tests/api/smoke` and `test/cli` directories. The above script will
skip if it can't resolve the file path to a single result. Once pytest-xdist is
released with the patch to the bug this step won't be necessary anymore.

All the above commands were to prepare the jUnit XML so that Betelgeuse can match a test result on the jUnit with the test on the source code that produced it. So now we can generate a XML file with the results to be imported by Polarion.

Before doing that, let's clarify some of the custom fields that are defined on
the AnsibleTower Polarion project for Test Runs (the entity created when the
test results are imported). These custom fields were created to map the test
environment so we can specify the Ansible Core version used, if it was a bundle
or plain install, if it was a cluster or standalone deployment and which
operating system Tower was deployed.

The test run information can be define by the following variables:

* `TEST_RUN_ANSIBLEVERSION`: for example `stable-2.8`
* `TEST_RUN_BUNDLE`: `true` if bundle install, `false` otherwise
* `TEST_RUN_CLUSTER`: `true` if cluster deployment, `false` othewise
* `TEST_RUN_ID`: the convention is like the following `Ansible Tower {version}
  - [Cluster|Standalone] - [Bundle|Plain] - Ansible {ansibleversion} - {os}`,
  for example, `Ansible Tower 3.6.0 - Standalone - Plain - Ansible stable-2.8 -
  rhel-8.0-x86_64`.
* `TEST_RUN_OS`: for example `rhel-8.0-x86_64`
* `TEST_RUN_PLANNEDIN`: the release ID on Polarion. The convention is
  `Ansible_Tower_3_6_0` for Ansible Tower 3.6.0, `Ansible_Tower_3_6_1` for
  Ansible Tower 3.6.1 and so on. Basically replace spaces and dots with an
  underscore.

See below an example on how to define the variables and generate the
`test-run.xml` file under the `reports/betelgeuse/`directory:

```console
$ JUNIT_PATH=junit-report-updated.xml \
  TEST_RUN_ANSIBLEVERSION="stable-2.8" \
  TEST_RUN_BUNDLE=false \
  TEST_RUN_CLUSTER=false \
  TEST_RUN_OS="rhel-8.0-x86_64" \
  TEST_RUN_TOWERVERSION="3.6.0" \
  ./tools/betelgeuse/scripts/gen-test-run
```

Finally the test results can be imported into Polarion:

```console
$ ./tools/betelgeuse/scripts/polarion-import xunit reports/betelgeuse/test-run.xml
