import os
import yaml
import glob
import logging
from py.path import local


log = logging.getLogger(__name__)


_file_pattern_cache = {}
_file_path_cache = {}


class Loader(yaml.Loader):

    file_pattern_cache = _file_pattern_cache
    file_path_cache = _file_path_cache

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
        if file_pattern in self.file_pattern_cache:
            return self.file_pattern_cache[file_pattern]

        data = dict()
        for file_path in glob.glob(file_pattern):
            file_path = os.path.abspath(file_path)
            if file_path in self.file_path_cache:
                path_data = self.file_path_cache[file_path]
            else:
                with open(file_path, 'r') as f:
                    path_data = yaml.load(f, Loader)
                self.file_path_cache[file_path] = path_data
            data.update(path_data)

        self.file_pattern_cache[file_pattern] = data
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
