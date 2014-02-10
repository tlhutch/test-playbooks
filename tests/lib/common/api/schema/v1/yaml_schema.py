#!/usr/bin/env python

import sys
import yaml
import imp
import os.path
import json
import glob
import jsonschema
import fnmatch

class Loader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)
        Loader.add_constructor('!include', Loader.include)
        Loader.add_constructor('!import',  Loader.include)

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
            for k,v in self.construct_mapping(node).iteritems():
                result[k] = self.extractFile(v)
            return result

        else:
            print "Error:: unrecognised node type in !include statement"
            raise yaml.constructor.ConstructorError

    def extractFile(self, filename):
        file_pattern = os.path.join(self._root, filename)
        data = dict()
        for filepath in glob.glob(file_pattern):
            with open(filepath, 'r') as f:
                data.update(yaml.load(f, Loader))
        return data

def read_and_close(fname):
    fd = open(fname, 'r')
    buf = fd.read()
    fd.close()
    return buf

if __name__ == "__main__":

    json_pattern = None
    if len(sys.argv) > 1:
        json_pattern = sys.argv[1:]

    # Look for all files ending in '.json'
    for json_file in glob.glob('*.json'):

        # If a file pattern was supplied, check for matches
        if json_pattern and not any([fnmatch.fnmatch(json_file, p) for p in json_pattern]):
            continue

        # Find corresponding YAML validation
        (json_name, json_ext) = os.path.splitext(json_file)
        yaml_file = json_name + '.yml'
        if not os.path.isfile(yaml_file):
            print "Skipping: %s ... no YAML validation file found" % json_file
            continue

        print "Validating: %s using %s ..." % (json_file, yaml_file)
        module = imp.load_source('api', json_file)

        schema = yaml.load(open(yaml_file, 'r'), Loader=Loader)
        jsonschema.validate(module.api, schema, format_checker=jsonschema.FormatChecker())

    # Remove any jsonc files
    for jsonc in glob.glob('*.jsonc'):
        os.unlink(jsonc)
