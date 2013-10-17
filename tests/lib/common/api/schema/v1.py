from common.api.schema import Awx_Schema

class Awx_Schema_v1(Awx_Schema):
    version = 'v1'
    component = '/api'

    def __init__(self):
        Awx_Schema.__init__(self)

        self.definitions['id'] = dict(type='number', minimum=1)
        self.definitions['summary_fields_inventory'] = {
            'type': 'object',
            'required': ['name', 'description', 'has_active_failures', 'hosts_with_active_failures',],
            'additionalProperties': False,
            'properties': {
                'name':                         { 'type': 'string', },
                'description':                  { 'type': 'string', },
                'has_active_failures':          { 'type': 'boolean', },
                'has_inventory_sources':        { 'type': 'boolean', },
                'hosts_with_active_failures':   { 'type': 'number', 'minimum': 0, },
            },
        }
        self.definitions['summary_fields_credential'] = {
            'type': 'object',
            'required': ['name', 'description', ],
            'additionalProperties': False,
            'properties': {
                'name':        { 'type': 'string', },
                'description': { 'type': 'string', },
            },
        }
        self.definitions['summary_fields_job_template'] = {
            'type': 'object',
            'required': ['name', 'description', ],
            'additionalProperties': False,
            'properties': {
                'name':        { 'type': 'string', },
                'description': { 'type': 'string', },
            },
        }
        self.definitions['enum_launch_type'] = {
            'enum': [ '', 'manual', 'callback', 'scheduled', ]
        }
        self.definitions['enum_launch_status'] = {
            'enum': [ '', 'new', 'pending', 'waiting', 'running', 'successul', 'failed', 'error', 'canceled' ]
        }
        self.definitions['enum_project_status'] = {
            'enum': [ '', 'ok', 'missing', 'never updated', 'updating', 'failed', 'successful' ]
        }
        self.definitions['summary_fields_project'] = {
            'type': 'object',
            'required': ['name', 'description', ],
            'additionalProperties': False,
            'properties': {
                'name':        { 'type': 'string', },
                'description': { 'type': 'string', },
                'status':      { 'enum': [ '', 'ok', 'missing', 'never updated', 'updating', 'failed', 'successful' ] },
            },
        }
        self.definitions['enum_source_status'] = {
            'enum': [ 'failed', 'never', 'none', 'successful', 'updating']
        }
        self.definitions['summary_fields_source'] = {
            'type': 'object',
            'required': ['source', 'status'],
            'additionalProperties': False,
            'properties': {
                'source': { 'type': 'string', },
                'status': { 'enum': [ 'failed', 'never', 'none', 'successful', 'updating'] },
            },
        }

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
                'summary_fields': { 'type': 'object', }, # FIXME
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
            'required': ['id', 'url', 'related', 'summary_fields', 'created', 'modified', 'name', 'description', 'organization', 'variables', 'has_active_failures', 'hosts_with_active_failures', 'has_inventory_sources', 'total_inventory_sources', 'total_hosts', 'inventory_sources_with_failures', 'groups_with_active_failures', 'total_groups', ],

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
                'total_hosts': { 'type': 'number', 'minimum': 0, },
                'groups_with_active_failures': { 'type': 'number', 'minimum': 0, },
                'total_groups': { 'type': 'number', 'minimum': 0, },
                'total_inventory_sources': { 'type': 'number', 'minimum': 0, },
                'has_inventory_sources': { 'type': 'boolean', },
                'inventory_sources_with_failures': { 'type': 'number', 'minimum': 0, },
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
            'required': ['id', 'url', 'created', 'modified', 'name', 'description', 'inventory', 'variables', 'has_active_failures', 'hosts_with_active_failures', 'has_inventory_sources', 'related', 'summary_fields', 'total_hosts', 'groups_with_active_failures', 'total_groups'],
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
                'has_inventory_sources': { 'type': 'boolean', },
                'total_hosts': { 'type': 'number', 'minimum': 0, },
                'groups_with_active_failures': { 'type': 'number', 'minimum': 0, },
                'total_groups':{ 'type': 'number', 'minimum': 0, },
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
                            '$ref': '#/definitions/summary_fields_inventory',
                        },
                        "inventory_source": {
                            '$ref': '#/definitions/summary_fields_source',
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

        self.definitions['summary_fields_group'] = {
            'type': 'object',
            'required': [ 'id', 'name', ],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'name': { 'type': 'string', },
            },
        }

        self.definitions['summary_fields_group_list'] = {
            'type': 'array',
            'minItems': 0,
            'uniqueItems': True,
            'items': {
                '$ref': '#/definitions/summary_fields_group',
            },
        }

        self.definitions['host'] = {
            'type': 'object',
            'required': [ 'id', 'url', 'created', 'modified', 'name', 'description', 'inventory', 'variables', 'enabled', 'has_active_failures', 'has_inventory_sources', 'last_job', 'last_job_host_summary', 'related', 'summary_fields', ],
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
                'enabled': { 'type': 'boolean', },
                'has_active_failures': { 'type': 'boolean', },
                'has_inventory_sources': { 'type': 'boolean', },
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

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['credential'] = {
            'type': 'object',
            'required': [ 'id', 'name', 'url', 'created', 'modified', 'description', 'ssh_username', 'ssh_password', 'ssh_key_data', 'ssh_key_unlock', 'sudo_username', 'sudo_password', 'user', 'team', 'related', 'summary_fields',],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'name': { 'type': 'string', },
                'url': { 'type': 'string', 'format': 'uri', },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'description': { 'type': 'string', },
                'ssh_username': { 'type': 'string', },
                'ssh_password': { 'type': 'string', },
                'ssh_key_data': { 'type': 'string', },
                'ssh_key_unlock': { 'type': 'string', },
                'sudo_username': { 'type': 'string', },
                'sudo_password': { 'type': 'string', },
                'user': { 'type': 'number', 'minimum': 1, },
                'team': { 'type': ['number', 'null'], },
                'related': {
                    'type': 'object',
                    'required': ['user'],
                    'additionalProperties': False,
                    'properties': {
                        'user': { 'type': 'string', 'format': 'uri' },
                    },
                },
                'summary_fields': {
                    'type': 'object',
                    'required': ['user'],
                    'additionalProperties': False,
                    'properties': {
                        'user': {
                            'type': 'object',
                            'required': ['username', 'first_name', 'last_name'],
                            'additionalProperties': False,
                            'properties': {
                                'username': { 'type': 'string' },
                                'first_name': { 'type': 'string' },
                                'last_name': { 'type': 'string' },
                            },
                        },
                    },
                },
            },
        }

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/credential',
        })

class Awx_Schema_v1_Projects(Awx_Schema_v1):
    component = '/projects'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['project'] = {
            'type': 'object',
            'required': [ 'id', 'name', 'url', 'created', 'modified', 'last_updated', 'description', 'last_update_failed', 'status', 'summary_fields', 'local_path', 'scm_type', 'scm_url', 'scm_branch', 'scm_clean', 'scm_delete_on_update', 'scm_delete_on_next_update', 'scm_update_on_launch', 'scm_username', 'scm_password', 'scm_key_data', 'scm_key_unlock',],
            'additionalProperties': False,
            'properties': {
                'id': { 'type': 'number', 'minimum': 1, },
                'name': { 'type': 'string', },
                'url': { 'type': 'string', 'format': 'uri', },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'last_updated': { 'type': 'string', 'format': 'date-time', },
                'description': { 'type': 'string', },
                'last_update_failed': { 'type': 'boolean', },
                'status': { 'enum': [ '', 'ok', 'missing', 'never updated', 'updating', 'failed', 'successful' ] },
                'summary_fields': { 'type': 'object', },
                'local_path': { 'type': 'string', 'format': 'uri', },
                'scm_type': { 'type': ['string', 'null',] },
                'scm_url': { 'type': 'string', },
                'scm_branch': { 'type': 'string', },
                'scm_clean': { 'type': 'boolean', },
                'scm_delete_on_update': { 'type': 'boolean', },
                'scm_delete_on_next_update': { 'type': 'boolean', },
                'scm_update_on_launch': { 'type': 'boolean', },
                'scm_username': { 'type': 'string', },
                'scm_password': { 'type': 'string', },
                'scm_key_data': { 'type': 'string', },
                'scm_key_unlock': { 'type': 'string', },
                'related': {
                    'type': 'object',
                    'required': ['created_by', 'organizations', 'project_updates', 'playbooks', 'update', 'teams'],
                    'additionalProperties': False,
                    'properties': {
                        'created_by':       { 'type': 'string', 'format': 'uri', },
                        'organizations':       { 'type': 'string', 'format': 'uri', },
                        'project_updates':       { 'type': 'string', 'format': 'uri', },
                        'playbooks':       { 'type': 'string', 'format': 'uri', },
                        'update':       { 'type': 'string', 'format': 'uri', },
                        'teams':       { 'type': 'string', 'format': 'uri', },
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
                        '$ref': '#/definitions/project',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/project',
        })

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['local_path', ],
            'additionalProperties': False,
            'properties': {
                "local_path": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Invalid path choice$',
                    },
                },
            },
        }

class Awx_Schema_v1_Job_templates(Awx_Schema_v1):
    component = '/job_templates'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['job_template'] = {
            'type': 'object',
            'required': [ 'id', 'name', 'url', 'description', 'created', 'modified', 'job_type', 'inventory', 'project', 'playbook', 'credential', 'forks', 'verbosity', 'limit', 'extra_vars', 'job_tags', 'host_config_key', 'related', 'summary_fields', ],
            'additionalProperties': False,
            'properties': {
                'id': { '$ref': '#/definitions/id', },
                'name': { 'type': 'string', },
                'url': { 'type': 'string', 'format': 'uri', },
                'description': { 'type': 'string', },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'job_type': { 'enum': ['run', 'check'], },
                'inventory': { '$ref': '#/definitions/id', },
                'project': { '$ref': '#/definitions/id', },
                'playbook': { 'type': 'string', 'pattern': '.*\.(yaml|yml)' },
                'credential': { '$ref': '#/definitions/id', },
                'forks': { 'type': 'number', 'minimum': 0 },
                'verbosity': { 'type': 'number', 'minimum': 0 },
                'limit': { 'type': 'string', },
                'extra_vars': { 'type': 'string', },
                'job_tags': { 'type': 'string', },
                'host_config_key': { 'type': 'string', },
                'related': {
                    'type': 'object',
                    'required': [ 'created_by', 'project', 'jobs', 'inventory', 'credential',],
                    'additionalProperties': False,
                    'properties': {
                        'created_by': { 'type': 'string', 'format': 'uri' },
                        'project': { 'type': 'string', 'format': 'uri' },
                        'jobs': { 'type': 'string', 'format': 'uri' },
                        'inventory': { 'type': 'string', 'format': 'uri' },
                        'credential': { 'type': 'string', 'format': 'uri' },
                    },
                },
                'summary_fields':  {
                    'type': 'object',
                    'required': ['inventory', 'project', 'credential',],
                    'additionalProperties': False,
                    'properties': {
                        "inventory": {
                            '$ref': '#/definitions/summary_fields_inventory',
                        },
                        "project": {
                            '$ref': '#/definitions/summary_fields_project',
                        },
                        "credential": {
                            '$ref': '#/definitions/summary_fields_credential',
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
                        '$ref': '#/definitions/job_template',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/job_template',
        })

    @property
    def duplicate(self):
        return {
            '$schema': 'http://json-schema.org/draft-04/schema#',
            'type': 'object',
            'required': ['name', ],
            'additionalProperties': False,
            'properties': {
                "name": {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'pattern': '^Job template with this Name already exists.',
                    },
                },
            },
        }

class Awx_Schema_v1_Jobs(Awx_Schema_v1):
    component = '/jobs'

    def __init__(self):
        Awx_Schema_v1.__init__(self)

        self.definitions['job'] = {
            'type': 'object',
            'required': [ 'id', 'name', 'url', 'description', 'created', 'modified', 'job_type', 'inventory', 'project', 'playbook', 'credential', 'forks', 'verbosity', 'limit', 'extra_vars', 'job_tags', 'job_template', 'launch_type', 'status', 'failed', 'result_stdout', 'result_traceback', 'passwords_needed_to_start', 'job_args', 'job_cwd', 'job_env', 'related', 'summary_fields', ],
            'additionalProperties': False,
            'properties': {
                'id': { '$ref': '#/definitions/id', },
                'name': { 'type': 'string', },
                'url': { 'type': 'string', 'format': 'uri', },
                'description': { 'type': 'string', },
                'created':  { 'type': 'string', 'format': 'date-time', },
                'modified': { 'type': 'string', 'format': 'date-time', },
                'job_type': { 'enum': ['run', 'check'], },
                'inventory': { '$ref': '#/definitions/id', },
                'project': { '$ref': '#/definitions/id', },
                'playbook': { 'type': 'string', 'pattern': '.*\.(yaml|yml)' },
                'credential': { '$ref': '#/definitions/id', },
                'forks': { 'type': 'number', 'minimum': 0 },
                'verbosity': { 'type': 'number', 'minimum': 0 },
                'limit': { 'type': 'string', },
                'extra_vars': { 'type': 'string', },
                'job_tags': { 'type': 'string', },
                'job_template': { '$ref': '#/definitions/id', },
                'launch_type': { '$ref': '#/definitions/enum_launch_type', },
                'status': { '$ref': '#/definitions/enum_launch_status', },
                'failed': { 'type': 'boolean', },
                'result_stdout': { 'type': 'string', },
                'result_traceback': { 'type': 'string', },
                'passwords_needed_to_start': {
                    'type': 'array',
                    'minItems': 0,
                    'uniqueItems': True,
                    'items': {
                        'type': 'string',
                        'uniqueItems': True,
                        'enum': [ 'ssh_password', ],
                    },
                },
                'job_args': { 'type': 'string', },
                'job_cwd': { 'type': 'string', },
                'job_env': {
                    'type': 'object',
                    # FIXME - add fields
                },
                'related': {
                    'type': 'object',
                    'required': [ 'project', 'job_host_summaries', 'created_by', 'credential', 'job_events', 'inventory', 'job_template', 'start', 'cancel',],
                    'additionalProperties': False,
                    'properties': {
                        'created_by': { 'type': 'string', 'format': 'uri' },
                        'project': { 'type': 'string', 'format': 'uri', },
                        'job_host_summaries': { 'type': 'string', 'format': 'uri', },
                        'credential': { 'type': 'string', 'format': 'uri', },
                        'job_events': { 'type': 'string', 'format': 'uri', },
                        'inventory': { 'type': 'string', 'format': 'uri', },
                        'job_template': { 'type': 'string', 'format': 'uri', },
                        'start': { 'type': 'string', 'format': 'uri', },
                        'cancel': { 'type': 'string', 'format': 'uri', },
                    },
                },
                'summary_fields':  {
                    'type': 'object',
                    'required': ['inventory', 'project', 'credential',],
                    'additionalProperties': False,
                    'properties': {
                        "inventory": {
                            '$ref': '#/definitions/summary_fields_inventory',
                        },
                        "project": {
                            '$ref': '#/definitions/summary_fields_project',
                        },
                        "credential": {
                            '$ref': '#/definitions/summary_fields_credential',
                        },
                        "job_template": {
                            '$ref': '#/definitions/summary_fields_job_template',
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
                        '$ref': '#/definitions/job',
                    },
                },
            },
        })

    @property
    def post(self):
        return self.format_schema({
            '$schema': 'http://json-schema.org/draft-04/schema#',
            '$ref': '#/definitions/job',
        })

class Awx_Schema_v1_Teams(Awx_Schema_v1):
    component = '/teams'

class Awx_Schema_v1_Config(Awx_Schema_v1):
    component = '/config'

class Awx_Schema_v1_Me(Awx_Schema_v1):
    component = '/me'

class Awx_Schema_v1_Authtoken(Awx_Schema_v1):
    component = '/authtoken'
