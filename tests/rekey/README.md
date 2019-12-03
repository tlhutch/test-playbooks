Tests located here are meant to be run to verify that the `awx-manage
regenerate_secret_key` with the changes to the installer works as expected.

To run these tests first make sure to to load the data before the rekey process
by running:

```console
$ AWXKIT_PREVENT_TEARDOWN=1 pytest -c config/api.cfg [...] tests/rekey/test_load.py
```

It is important to set or export the `AWXKIT_PREVENT_TEARDOWN` variable so the
entities created are not deleted and will be available when verifying after the
rekey process.

With the data loaded, run the rekey process. This can be done by running
`./setup.sh -k` on the machine and place where the Tower installer was run when
deploying it. For an example check the `tools/jenkins/scripts/rekey.sh` to see
how this is done on Jenkins.

After the rekey process, check if all the loaded information still available and
are able to be decryped with the new `SECRET_KEY` by running the following:

```console
$ pytest -c config/api.cfg [...] tests/rekey/test_verify.py
```

Make sure to run pytest from the same working directory where the load was run
because it creates a `rekey-data.yml` file to store the created objects IDs and
be able to verify later.
