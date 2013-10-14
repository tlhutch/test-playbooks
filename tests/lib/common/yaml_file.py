import os
import yaml
from py.path import local
from common.randomness import RandomizeValues

def load_file(filename=None):
    """
    Loads a YAML file from the given filename

    If the filename is omitted or None, attempts will be made to load it from
    its normal location in the parent of the utils directory.

    The awx_data dict loaded with this method supports value randomization,
    thanks to the RandomizeValues class. See that class for possible options

    Example usage in data.yaml (quotes are important!):

    top_level:
        list:
            - "{random_str}"
            - "{random_int}"
            - "{random_uuid}"
        random_thing: "{random_string:24}"
    """
    if filename is None:
        this_file = os.path.abspath(__file__)
        path = local(this_file).new(basename='../data.yaml')
    else:
        path = local(filename)

    if path.check():
        fp = path.open()
        data = yaml.load(fp)
        return RandomizeValues.from_dict(data)
    else:
        msg = 'Usable to load data file at %s' % path
        raise Exception(msg)

