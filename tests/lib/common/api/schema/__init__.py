import sys
import re
import inspect
import pkgutil
import logging
import jsonschema
from collections import defaultdict
from urlparse import urlparse


class SchemaVersionNotFound(Exception):
    pass


class SchemaResourceNotFound(Exception):
    pass


class SchemaRequestNotFound(Exception):
    pass


class Schema_Collection(object):
    def __init__(self):
        self.schemas = defaultdict(dict)
        self._schema_cache = {}

    def add_schema(self, schema):
        assert issubclass(cls, Schema_Base), 'Unknown schema parameter type: %s' % type(schema)
        assert hasattr(schema, 'version')
        assert hasattr(schema, 'resource')

        logging.debug("add_schema version:%s, resource:%s" % (schema.version, schema.resource))
        self.schemas[schema.version][schema.resource] = schema()

    def get_schema(self, version, resource, request='get'):
        # Remove any query string parameters '?...'
        resource = urlparse(resource).path
        # Lowercase the request string
        request = request.lower()

        logging.debug("get_schema version:%s, request:%s, resource:%s" % (version, request, resource))

        if version not in self.schemas:
            if len(self.schemas) == 1:
                version = self.schemas.keys()[0]
            else:
                raise SchemaVersionNotFound(
                    "No schema version '%s' found. Choices include: %s"
                    % (version, self.schemas.keys())
                )

        # Determine whether provided resource matches as a regular expression
        if resource not in self.schemas[version]:
            for match_re in self.schemas[version]:
                if re.match(match_re + '$', resource):
                    resource = match_re
                    break

        if resource in self._schema_cache:
            if request in self._schema_cache[resource]:
                logging.debug("get_schema version:%s, request:%s, resource:%s cache hit" % (version, request, resource))
                return self._schema_cache[resource][request]
        else:
            self._schema_cache[resource] = {}

        # Assert the resource exists
        if resource not in self.schemas[version]:
            raise SchemaResourceNotFound(
                "No schema resource '%s' found. Choices include: %s"
                % (resource, self.schemas[version].keys())
            )

        # Validate the schema request type (get, post, put, patch etc...)
        if not hasattr(self.schemas[version][resource], request):
            properties = [meth[0]
                          for meth in inspect.getmembers(self.schemas[version][resource].__class__, lambda x: isinstance(x, property))]
            raise SchemaRequestNotFound(
                "No schema request '%s' found. Choices include: %s"
                % (request, properties)
            )

        schema = getattr(self.schemas[version][resource], request)
        self._schema_cache[resource][request] = schema
        return schema


class Schema_Base(object):
    '''
    FIXME
    '''
    @property
    def get(self):
        raise NotImplementedError('Implement in a sub-class')

    @property
    def post(self):
        raise NotImplementedError('Implement in a sub-class')

    @property
    def put(self):
        raise NotImplementedError('Implement in a sub-class')

    @property
    def patch(self):
        raise NotImplementedError('Implement in a sub-class')

    @property
    def head(self):
        raise NotImplementedError('Implement in a sub-class')

    @property
    def options(self):
        raise NotImplementedError('Implement in a sub-class')


def __find_schema_versions(path, prefix):
    '''
    FIXME
    '''
    for module_loader, name, ispkg in pkgutil.iter_modules(path, prefix):
        logging.debug("__find_schema_versions: %s, %s, %s" % (module_loader, name, ispkg))
        if ispkg:
            yield (module_loader, name, ispkg)
        else:
            yield (module_loader, name, ispkg)


def validate(data, resource, request, version=None):
    '''
    FIXME
    '''
    # Make debugging easier if we accidentally pass the wrong schema type
    schema = schema_collection.get_schema(version, resource, request)
    assert isinstance(schema, dict), \
        "Expecting dict, found %s" % type(schema)

    try:
        jsonschema.validate(data, schema, format_checker=jsonschema.FormatChecker())
    except jsonschema.ValidationError:
        sys.stderr.write("Failure validating resource:%s, version:%s, request:%s\n" % (resource, version, request))
        exc_info = sys.exc_info()
        raise exc_info[1], None, exc_info[2]


if __name__ == 'common.api.schema':
    prefix = __name__ + '.'
    schema_versions = __find_schema_versions(__path__, prefix)
    schema_collection = Schema_Collection()

    for (module_loader, name, ispkg) in schema_versions:
        if name not in sys.modules:
            logging.debug("__import__(%s, %s)" % (name, [name]))
            loaded_mod = __import__(name, fromlist=[name])

            # Load classes from imported module
            if ispkg:
                for (name, cls) in inspect.getmembers(loaded_mod, inspect.isclass):
                    if issubclass(cls, Schema_Base) and hasattr(cls, 'resource'):
                        logging.debug("load_commands() - found '%s'" % name)
                        schema_collection.add_schema(cls)

            # Import schema from a module
            else:
                logging.debug("skipping module:%s" % name)
