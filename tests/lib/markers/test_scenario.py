import py
import pytest

'''
Automatically xfail remaining tests if previous test failed.  Tests will
continue to run if a result is skip or xfail.

For more information, refer to
http://stackoverflow.com/questions/12411431/pytest-how-to-skip-the-rest-of-tests-in-the-class-if-one-has-failed/12579625#12579625
'''

def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None \
           and not any([call.excinfo.errisinstance(py.test.xfail.Exception),
                       call.excinfo.errisinstance(py.test.skip.Exception)]):
            parent = item.parent
            parent._previousfailed = item

def pytest_runtest_setup(item):
    previousfailed = getattr(item.parent, "_previousfailed", None)
    if previousfailed is not None:
        pytest.xfail("previous test failed (%s)" %previousfailed.name)
