import os
import yaml
import glob
import logging
from py.path import local


log = logging.getLogger(__name__)


class Loader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)
        Loader.add_constructor('!include', Loader.include)
        Loader.add_constructor('!import', Loader.include)

    def include(self, node):
        if isinstance(node, yaml.ScalarNode):
            return self.extractFile(self.construct_scalar(node))

        elif isinstance(node, yaml.SequenceNode):
            result = []
            for filename in self.construct_sequence(node):
                result += self.extractFile(filename)
            return result

        elif isinstance(node, yaml.MappingNode):
            result = {}
            for k, v in self.construct_mapping(node).iteritems():
                result[k] = self.extractFile(v)
            return result

        else:
            log.error("unrecognised node type in !include statement")
            raise yaml.constructor.ConstructorError

    def extractFile(self, filename):
        file_pattern = os.path.join(self._root, filename)
        data = dict()
        for filepath in glob.glob(file_pattern):
            with open(filepath, 'r') as f:
                data.update(yaml.load(f, Loader))
        return data


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
        # FIXME - support load_all()
        return yaml.load(fp, Loader=Loader)
    else:
        msg = 'Usable to load data file at %s' % path
        raise Exception(msg)
