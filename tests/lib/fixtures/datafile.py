import os
import pytest
from string import Template
from tempfile import NamedTemporaryFile


# Collection for storing unique combinations of data file paths
# and filenames for usage reporting after a completed test run
seen_data_files = set()


@pytest.fixture(scope="module")
def datafile(request):
    """datafile fixture, with templating support

    Usage
    =====

    Given a filename, it will attempt to open the given file from the
    test's directory using a precedence list. For example, this:

        datafile('testfile') # in tests/subdir/test_module_name.py

    Will return a file object for the first file that exists using the following order:

        tests/subdir/data/testfile
        tests/subdir/testfile

    Given a filename with a leading slash, it will attempt to load the file
    relative to the root of the data dir. For example, this:

        datafile('/common/testfile') # in tests/subdir/test_module_name.py

    Would return a file object representing this file:

        data/common/testfile
        common/testfile

    """
    return FixtureDataFile(request)


class FixtureDataFile(object):
    def __init__(self, request):
        self.base_path = str(request.session.fspath)
        self.testmod_path = str(request.fspath)

    def __call__(self, filename, replacements=None):
        if filename.startswith('/'):
            complete_path = find_data_file(
                filename.strip('/'), self.base_path)
        else:
            complete_path = find_data_file(
                filename, self.base_path, self.testmod_path)

        seen_data_files.add(complete_path)

        return load_data_file(complete_path, replacements)


def load_data_file(filename, replacements=None):
    """Opens the given filename, returning a file object

    If a base_path string is passed, filename will be loaded from there
    If a replacements mapping is passed, the loaded file is assumed to
        be a template[1]. In this case the replacements mapping will be
        used in that template's subsitute method.

    [1]: http://docs.python.org/2/library/string.html#template-strings

    """
    if replacements is None:
        return open(filename)
    else:
        with open(filename) as template_file:
            template = Template(template_file.read())

        output = template.substitute(replacements)

        outfile = NamedTemporaryFile()
        outfile.write(output)
        outfile.flush()
        outfile.seek(0)
        return outfile


def find_data_file(filename, base_path, testmod_path=None):
    if testmod_path:
        for attempt in [os.path.join(base_path, os.path.dirname(testmod_path), 'data', filename),
                        os.path.join(base_path, os.path.dirname(testmod_path), filename), ]:
            if os.path.isfile(attempt):
                new_path = attempt
                break
    else:
        # No testmod_path? Well that's a lot easier!
        # Just join it with the data root, minus its leading slash
        for attempt in [os.path.join(base_path, 'data', filename),
                        os.path.join(base_path, filename), ]:
            if os.path.isfile(attempt):
                new_path = attempt

    return new_path
