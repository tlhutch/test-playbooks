'''
Note: We include ansible + psutil in both environments so that the streams aren't crossed.
The streams get crossed when the ansible virtualenv contains a different version of python
than the version in the custom virtualenv. When a package is not found in the custom
virtualenv, the ansible virtualenv is the fallback virtualenv. This is problematic when
the python lib found doesn't support both versions of python.
Second Note: Collections were only added in Ansible 2.9, and are rapidly changing
with relevant fixes as of the time this was written, so the current version is used.
'''

# NOTE: This actually doesn't do the creation and installation of the
# virtualenvs, this is purely metadata for the tests to know where the
# virtualenv is
CUSTOM_VENVS = [
    {
        'name': 'python2_tower_modules',
        'python_interpreter': 'python2'
    },
    {
        'name': 'python3_tower_modules',
        'python_interpreter': 'python36'
    },
]


CUSTOM_VENVS_NAMES = [venv['name'] for venv in CUSTOM_VENVS]
