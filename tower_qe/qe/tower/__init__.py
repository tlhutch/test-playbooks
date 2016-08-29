from distutils.version import LooseVersion


def version_cmp(x, y):
    return LooseVersion(x).__cmp__(y)
