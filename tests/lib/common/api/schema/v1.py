from common.api.schema import Awx_Schema

class Awx_Schema_v1(Awx_Schema):
    version = 'v1'
    component = '/api'

    @property
    def get(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'properties': {
                'available_versions': { 'type': 'object', },
                'description': { 'type': 'string', },
                'current_version': { 'type': 'string', },
            },
            'required': ['available_versions', 'description', 'current_version'],
            'additionalProperties': False,
        }

    @property
    def options(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                },
                'description': {
                    'type': 'string',
                },
                'renders': {
                    'type': 'array',
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                },
                'parses': {
                    'type': 'array',
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1,
                    "uniqueItems": True,
                },
            },
            'required': [ 'renders', 'parses' ],
            'additionalProperties': False,
        }

    @property
    def unauthorized(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'properties': {
                'detail': {
                    'type': 'string',
                },
            },
            'required': ['detail', ],
            'additionalProperties': False,
        }

    @property
    def bad_password(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'properties': {
                "username": {
                    'type': 'array',
                },
                "password": {
                    'type': 'array',
                },
            },
            'required': ['username', 'password', ],
            'additionalProperties': False,
        }

class Awx_Schema_v1_Organizations(Awx_Schema_v1):
    component = '/organizations'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['organization'] = {
            'type': 'object',
            'required': ['id', 'url', 'name', 'description', 'created', 'modified', 'summary_fields', 'related'],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'url': { 'type': 'string', 'format': 'uri'},
                'related': {
                    'type': 'object',
                    'required': ['created_by', 'admins', 'inventories', 'users', 'projects', 'teams',],
                    'additionalProperties': False,
                    'properties': {
                        'created_by':   { 'type': 'string', 'format': 'uri' },
                        'admins':       { 'type': 'string', 'format': 'uri' },
                        'inventories':  { 'type': 'string', 'format': 'uri' },
                        'users':        { 'type': 'string', 'format': 'uri' },
                        'projects':     { 'type': 'string', 'format': 'uri' },
                        'teams':        { 'type': 'string', 'format': 'uri' },
                    },
                },
                'summary_fields': { 'type': 'object', },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'name': { 'type': 'string', },
                'description': { 'type': 'string', },
            },
        }

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'properties': {
                "name": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Organization with this Name already exists.$',
                    },
                },
            },
            'required': ['name', ],
            'additionalProperties': False,
        }

    @property
    def get(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['count', 'next', 'previous', 'results', ],
            'additionalProperties': False,
            'properties': {
                'count': { 'type': 'number', 'minimum': 0, },
                'next': { 'type': ['string','null'], },
                'previous': { 'type': ['string','null'], },
                'results': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        '$ref': '#/definitions/organization',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/organization',
        })

    @property
    def options(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            # 'required': ['', '', ''],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'description': {
                    'type': 'string',
                },
                'renders': {
                    'type': 'array',
                    "minItems": 1,
                    "uniqueItems": True
                },
                'parses': {
                    'type': 'array',
                    "minItems": 1,
                    "uniqueItems": True
                },
                'actions': {
                    'type': 'object',
                    'properties': {
                        'POST': {
                            'type': 'string',
                            'properties': {
                                'id': {
                                    'type': 'object',
                                },
                            },
                        },
                    },
                },
            },
        })


class Awx_Schema_v1_Me(Awx_Schema_v1):
    component = '/me'

class Awx_Schema_v1_Authtoken(Awx_Schema_v1):
    component = '/authtoken'

class Awx_Schema_v1_Jobs(Awx_Schema_v1):
    component = '/jobs'

class Awx_Schema_v1_Users(Awx_Schema_v1):
    component = '/users'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['user'] = {
            'type': 'object',
            'required': ['created', 'email', 'first_name', 'id', 'is_superuser', 'last_name', 'ldap_dn', 'related', 'url', 'username'],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'url': { 'type': 'string', 'format': 'uri'},
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'first_name': { 'type': 'string', },
                'last_name': { 'type': 'string', },
                'username': { 'type': 'string', },
                'ldap_dn': { 'type': 'string', },
                'is_superuser': { 'type': 'boolean', },
                'email': { 'type': 'string', 'format': 'email'},
                'related': {
                    'type': 'object',
                    'required': ['admin_of_organizations', 'credentials', 'organizations', 'permissions', 'projects', 'teams',],
                    'additionalProperties': False,
                    'properties': {
                        'admin_of_organizations':   { 'type': 'string', 'format': 'uri' },
                        'credentials':              { 'type': 'string', 'format': 'uri' },
                        'organizations':            { 'type': 'string', 'format': 'uri' },
                        'permissions':              { 'type': 'string', 'format': 'uri' },
                        'projects':                 { 'type': 'string', 'format': 'uri' },
                        'teams':                    { 'type': 'string', 'format': 'uri' },
                    },
                },
            },
        }

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['username', ],
            'additionalProperties': False,
            'properties': {
                "username": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^User with this Username already exists.$',
                    },
                },
            },
        }

    @property
    def get(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['count', 'next', 'previous', 'results', ],
            'additionalProperties': False,
            'properties': {
                'count': { 'type': 'number', 'minimum': 0, },
                'next': { 'type': ['string','null'], },
                'previous': { 'type': ['string','null'], },
                'results': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        '$ref': '#definitions/user',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/user',
        })

class Awx_Schema_v1_Inventories(Awx_Schema_v1):
    component = '/inventories'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['inventory'] = {
            'type': 'object',
            'required': ['id', 'url', 'related', 'summary_fields', 'created', 'modified', 'name', 'description', 'organization', 'variables', 'has_active_failures', 'hosts_with_active_failures'],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'url': { 'type': 'string', 'format': 'uri'},
                'related': {
                    'type': 'object',
                    'required': ['created_by', 'variable_data', 'root_groups', 'script', 'tree', 'hosts', 'groups', 'organization', 'inventory_sources',],
                    'additionalProperties': False,
                    'properties': {
                        "created_by":       { 'type': 'string', 'format': 'uri', },
                        "variable_data":    { 'type': 'string', 'format': 'uri', },
                        "root_groups":      { 'type': 'string', 'format': 'uri', },
                        "script":           { 'type': 'string', 'format': 'uri', },
                        "tree":             { 'type': 'string', 'format': 'uri', },
                        "hosts":            { 'type': 'string', 'format': 'uri', },
                        "groups":           { 'type': 'string', 'format': 'uri', },
                        "organization":     { 'type': 'string', 'format': 'uri', },
                        "inventory_sources":{ 'type': 'string', 'format': 'uri', },
                    },
                },
                'summary_fields':  {
                    'type': 'object',
                    'required': ['organization'],
                    'additionalProperties': False,
                    'properties': {
                        "organization": {
                            'type': 'object',
                            'required': ['name', 'description'],
                            'additionalProperties': False,
                            'properties': {
                                'name':        { 'type': 'string', },
                                'description': { 'type': 'string', },
                            },
                        },
                    },
                },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'name': { 'type': 'string', },
                'description': { 'type': 'string', },
                'organization': { 'type': 'number', 'minimum': 1, },
                'variables': { 'type': 'string', },
                'has_active_failures': { 'type': 'boolean', },
                'hosts_with_active_failures': { 'type': 'number', 'minimum': 0, },
            },
        }

    @property
    def get(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['count', 'next', 'previous', 'results', ],
            'additionalProperties': False,
            'properties': {
                'count': { 'type': 'number', 'minimum': 0, },
                'next': { 'type': ['string','null'], },
                'previous': { 'type': ['string','null'], },
                'results': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        '$ref': '#definitions/inventory',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/inventory',
        })

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['name', '__all__'],
            'additionalProperties': False,
            'properties': {
                "__all__": {
                    'type': 'array',
                    'minItems': 1,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Inventory with this Name and Organization already exists.$',
                    },
                },
                "name": {
                    'type': 'array',
                    'minItems': 1,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Inventory with this Name already exists.$',
                    },
                },
            },
        }


class Awx_Schema_v1_Groups(Awx_Schema_v1):
    component = '/groups'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['group'] = {
            'type': 'object',
            'required': ['id', 'url', 'created', 'modified', 'name', 'description', 'inventory', 'variables', 'has_active_failures', 'hosts_with_active_failures', 'related', 'summary_fields'],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'url': { 'type': 'string', 'format': 'uri'},
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'name': { 'type': 'string', },
                'description': { 'type': 'string', },
                'inventory': { 'type': 'number', 'minimum': 1, },
                'variables': { 'type': 'string', },
                'has_active_failures': { 'type': 'boolean', },
                'hosts_with_active_failures': { 'type': 'number', 'minimum': 0, },
                'related': {
                    'type': 'object',
                    'required': [ 'created_by', 'job_host_summaries', 'variable_data', 'inventory_source', 'job_events', 'potential_children', 'all_hosts', 'hosts', 'inventory', 'children',],
                    'additionalProperties': False,
                    'properties': {
                        "created_by":           { 'type': 'string', 'format': 'uri', },
                        "job_host_summaries":   { 'type': 'string', 'format': 'uri', },
                        "variable_data":        { 'type': 'string', 'format': 'uri', },
                        "inventory_source":     { 'type': 'string', 'format': 'uri', },
                        "job_events":           { 'type': 'string', 'format': 'uri', },
                        "potential_children":   { 'type': 'string', 'format': 'uri', },
                        "all_hosts":            { 'type': 'string', 'format': 'uri', },
                        "hosts":                { 'type': 'string', 'format': 'uri', },
                        "inventory":            { 'type': 'string', 'format': 'uri', },
                        "children":             { 'type': 'string', 'format': 'uri', },
                    },
                },
                'summary_fields':  {
                    'type': 'object',
                    'required': ['inventory', 'inventory_source'],
                    'additionalProperties': False,
                    'properties': {
                        "inventory": {
                            'type': 'object',
                            'required': ['name', 'description', 'has_active_failures', 'hosts_with_active_failures'],
                            'additionalProperties': False,
                            'properties': {
                                'name':        { 'type': 'string', },
                                'description': { 'type': 'string', },
                                'has_active_failures': { 'type': 'boolean', },
                                'hosts_with_active_failures': { 'type': 'number', 'minimum': 0, },
                            },
                        },
                        "inventory_source": {
                            'type': 'object',
                            'required': ['source', 'status'],
                            'additionalProperties': False,
                            'properties': {
                                'source': { 'type': 'string', },
                                'status': { 'enum': [ 'failed', 'never', 'none', 'successful', 'updating'] },
                            },
                        },
                    },
                },
            },
        }

    @property
    def get(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['count', 'next', 'previous', 'results', ],
            'additionalProperties': False,
            'properties': {
                'count': { 'type': 'number', 'minimum': 0, },
                'next': { 'type': ['string','null'], },
                'previous': { 'type': ['string','null'], },
                'results': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        '$ref': '#/definitions/group',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/group',
        })

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['__all__',],
            'additionalProperties': False,
            'properties': {
                "__all__": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Group with this Name and Inventory already exists.$',
                    },
                },
            },
        }

class Awx_Schema_v1_Hosts(Awx_Schema_v1):
    component = '/hosts'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['summary_fields_group_list'] = {
            'type': 'array',
            'minItems': 0,
            'uniqueItems': True,
            'items': {
                '$ref': '#/definitions/summary_fields_group',
            },
        }

        self.definitions['summary_fields_group'] = {
            'type': 'object',
            'required': [ 'id', 'name', ],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'name': { 'type': 'string', },
            },
        }

        self.definitions['summary_fields_inventory'] = {
            'type': 'object',
            'required': ['name', 'description', 'has_active_failures', 'hosts_with_active_failures',],
            'additionalProperties': False,
            'properties': {
                'name':                         { 'type': 'string', },
                'description':                  { 'type': 'string', },
                'has_active_failures':          { 'type': 'boolean', },
                'hosts_with_active_failures':   { 'type': 'number', 'minimum': 0, },
            },
        }

        self.definitions['host'] = {
            'type': 'object',
            'required': [ 'id', 'url', 'created', 'modified', 'name', 'description', 'inventory', 'variables', 'has_active_failures', 'last_job', 'last_job_host_summary', 'related', 'summary_fields', ],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'url': { 'type': 'string', 'format': 'uri'},
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'name': { 'type': 'string', },
                'description': { 'type': 'string', },
                'inventory': { 'type': 'number', 'minimum': 1, },
                'variables': { 'type': 'string', },
                'has_active_failures': { 'type': 'boolean', },
                'last_job': { 'type': ['string', 'null'] },
                'last_job_host_summary': { 'type': ['string', 'null'] },
                'related': {
                    'type': 'object',
                    'required': [ "created_by", "job_host_summaries", "variable_data", "job_events", "groups", "all_groups", "inventory",],
                    'additionalProperties': False,
                    'properties': {
                        "created_by":           { 'type': 'string', 'format': 'uri', },
                        "job_host_summaries":   { 'type': 'string', 'format': 'uri', },
                        "variable_data":        { 'type': 'string', 'format': 'uri', },
                        "job_events":           { 'type': 'string', 'format': 'uri', },
                        "groups":               { 'type': 'string', 'format': 'uri', },
                        "all_groups":           { 'type': 'string', 'format': 'uri', },
                        "inventory":            { 'type': 'string', 'format': 'uri', },
                    },
                },
                'summary_fields':  {
                    'type': 'object',
                    'required': ['inventory', 'groups', 'all_groups',],
                    'additionalProperties': False,
                    'properties': {
                        "inventory": {
                            '$ref': '#/definitions/summary_fields_inventory',
                        },
                        "all_groups": {
                            '$ref': '#/definitions/summary_fields_group_list',
                        },
                        "groups": {
                            '$ref': '#/definitions/summary_fields_group_list',
                        },
                    },
                },
            },
        }

    @property
    def get(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['count', 'next', 'previous', 'results', ],
            'additionalProperties': False,
            'properties': {
                'count': { 'type': 'number', 'minimum': 0, },
                'next': { 'type': ['string','null'], },
                'previous': { 'type': ['string','null'], },
                'results': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        '$ref': '#/definitions/host',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/host',
        })

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['__all__',],
            'additionalProperties': False,
            'properties': {
                "__all__": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Host with this Name and Inventory already exists.$',
                    },
                },
            },
        }


class Awx_Schema_v1_Credentials(Awx_Schema_v1):
    component = '/credentials'

class Awx_Schema_v1_Config(Awx_Schema_v1):
    component = '/config'

class Awx_Schema_v1_Projects(Awx_Schema_v1):
    component = '/projects'

class Awx_Schema_v1_Job_templates(Awx_Schema_v1):
    component = '/job_templates'

class Awx_Schema_v1_Teams(Awx_Schema_v1):
    component = '/teams'
