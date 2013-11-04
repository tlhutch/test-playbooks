import sys
import inspect
import pkgutil
import logging
import jsonschema
from collections import defaultdict

available_schemas = defaultdict(dict)

class Awx_Schema(object):
    def __init__(self):
        self.definitions = dict()
        # Raise if not-subclassed

    def format_schema(self, schema):
        '''
        If schema definitions are avaiable, merge them with the provided schema
        '''
        if self.definitions:
            return dict(schema.items() + \
                dict(definitions=self.definitions).items())
        else:
            return schema

# find available schema versions
def find_schema_modules(path, prefix):
    '''
    FIXME
    '''
    for module_loader, name, ispkg in pkgutil.iter_modules(path, prefix):
        if not ispkg:
            yield (module_loader, name, ispkg)

def get_schema(version=None, component=None, name=None):
    '''
    FIXME
    '''
    if version is None:
        if len(available_schemas) == 1:
            version = available_schemas.keys()[0]
        else:
            raise ValueError("No version parameter provided and multiple schema versions exist")

    if not available_schemas.has_key(version):
        raise Exception("No schema matching version '%s' found." % version)

    # Remove '/api' prefix
    if component.startswith('/api'):
        component = component[4:]

    # Remove '/v1' prefix
    if component.startswith('/'+version):
        component = component[len(version)+1:]

    # Remove trailing '/'
    if component.endswith('/'):
        component = component[:-1]

    if not available_schemas[version].has_key(component):
        raise Exception("No schema component matching '%s' found. " \
                        "Choices include: %s" % (component, available_schemas[version].keys()))

    if not hasattr(available_schemas[version][component], name):
        raise Exception("No schema attribute matching '%s' found. " \
                        "Choices include: %s" % (name, dir(available_schemas[version][component])))

    return getattr(available_schemas[version][component], name)

def validate(data, component, name, version=None):
    '''
    FIXME
    '''
    if version is None:
        if len(available_schemas) == 1:
            version = available_schemas.keys()[0]
        else:
            raise ValueError("No version parameter provided and multiple schema versions exist")

    # Make debugging easier if we accidentally pass the wrong schema type
    schema = get_schema(version, component, name)
    assert isinstance(schema, dict), \
        "Expecting dict, found %s" % type(schema)

    jsonschema.validate(data, schema,
        format_checker=jsonschema.FormatChecker())

if __name__ == 'common.api.schema':
    path = __path__[0]
    prefix = __name__ + '.'
    schema_versions = find_schema_modules([path], prefix)

    for (module_loader, name, ispkg) in schema_versions:
        if name not in sys.modules:
            # Import module
            logging.debug("__import__(%s, %s)" % (name, [name]))
            loaded_mod = __import__(name, fromlist=[name])

            # Load class from imported module
            for (name, cls) in inspect.getmembers(loaded_mod, inspect.isclass):
                if issubclass(cls, Awx_Schema) and cls != Awx_Schema \
                   and hasattr(cls, 'version') and hasattr(cls, 'component'):
                    logging.debug("load_commands() - found '%s'" % name)
                    logging.debug("available_schemas[%s][%s] = %s" % (cls.version, cls.component, name))
                    available_schemas[cls.version][cls.component] = cls()
                else:
                    logging.debug("load_commands() - skipping class '%s'" % name)
                    continue
