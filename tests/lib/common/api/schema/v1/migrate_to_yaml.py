#!/usr/bin/env python

import os
import sys
import inspect
import yaml

if os.path.isdir('../tests/lib'):
    sys.path.insert(0, '../tests/lib')

if os.path.isdir('tests/lib'):
    sys.path.insert(0, 'tests/lib')

if os.path.isdir('lib'):
    sys.path.insert(0, 'lib')

import common.api.schema

if len(sys.argv) != 3:
    print "Usage %s: <component> <request>" % sys.argv[0]
    sys.exit(1)

(component, method) = sys.argv[1:]

try:
    schema = common.api.schema.get_schema(version='v1', component=component, request=method.lower())
except Exception, e:
    print e
    sys.exit(1)

print schema
print yaml.dump(schema)
