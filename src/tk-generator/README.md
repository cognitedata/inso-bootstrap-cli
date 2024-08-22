## 240816 new config sketch

- new approach to config sketch
- pydantic v2 code to load and validate name-references
- TODO:
  - [x] resolve dependencies
  - [x] check for cycles
  - [ ] and order of resolution
  - [ ] cdf-tk config generation

### installation

```bash
cd git/inso-bootstrap-cli
# sharing pyproject.toml with general bootstrap-cli
poetry install --sync
poetry shell
```

### parse and validate example config

```bash
on 💻️spexryz5 inso-bootstrap-cli on  feat/command-export-to-cdftk [?] is 📦 v3.3.0 via 🐍 v3.11.9 (inso-bootstrap-cli-py3.11) 
➟  python -m src.tk-generator.tk_generator_config

scope_set_names: ['canvas', 'in-001', 'in-all', 'infield-admin-instances', 'infield-common-instances', 'infield-common-model', 'infield-guest-instances', 
'infield-rb-location-instances', 'src-all', 'uc-001', 'unscoped']
acl_set_names: ['governance', 'user', 'with-scoping', 'without-scoping']
acl_set_supported_names: ['annotations', 'assets', 'dataModelInstances', 'dataModels', 'datasets', 'digitalTwin', 'documentFeedback', 'documentPipelines', 
'entitymatching', 'events', 'extractionConfigs', 'extractionPipelines', 'extractionRuns', 'files', 'functions', 'geospatial', 'geospatialCrs', 'governance',
'groups', 'labels', 'monitoringTasks', 'notifications', 'projects', 'raw', 'relationships', 'robotics', 'securityCategories', 'seismic', 'sequences', 
'sessions', 'templateGroups', 'templateInstances', 'threed', 'timeSeries', 'timeSeriesSubscriptions', 'transformations', 'types', 'user', 'wells', 
'with-scoping', 'without-scoping', 'workflowOrchestration']
action_set_names: ['GOVERNANCE', 'OWNER', 'READ']
capability_set_names: ['canvas', 'governance', 'in-001-owner', 'infield-admin', 'infield-common', 'infield-rb-user', 'uc-001-owner']

/home/arwapet/.cache/pypoetry/virtualenvs/inso-bootstrap-cli-TtUlhYUa-py3.11/lib/python3.11/site-packages/pydantic/main.py:347: UserWarning: Pydantic serializer warnings:
  Expected `ExplicitScopes` but got `list` - serialized value may not be as expected
  return self.__pydantic_serializer__.to_python(
{
    'idp_cdf_mapping': [
        {
            'project': 'equinor-dev',
            'groups': [
                {
                    'name': 'cdf:uc:001:demand:owner',
                    'capability_sets': ['uc-001-owner', 'canvas'],
                    'metadata': {
                        'Dataops_created': '2024-01-12 10:23:31',
                        'Dataops_source': 'bootstrap-cli v3.3.0',
                        'idp_source_id': 'acd2fe35-aa51-45a7-acef-0d54e2b6b6a8',
                        'idp_source_name': 'CDF_DEV_ALLPROJECTS_READ'
                    },
                    'sourceId': 'acd2fe35-aa51-45a7-acef-0d54e2b6b6a8'
                },
                {
                    'name': 'cdf:root',
                    'capability_sets': ['governance'],
                    'metadata': {
                        'Dataops_created': '2024-01-12 10:23:31',
                        'Dataops_source': 'bootstrap-cli v3.3.0',
                        'idp_source_id': 'acd2fe35-aa51-45a7-acef-0d54e2b6b6a8',
                        'idp_source_name': 'CDF_DEV_ALLPROJECTS_READ'
                    },
                    'sourceId': 'acd2fe35-aa51-45a7-acef-0d54e2b6b6a8'
                }
            ]
        }
    ],
    'action_sets': [
        {
            'name': 'OWNER',
            'description': '',
            'action_mapping': {
                'annotations': ['READ', 'WRITE', 'SUGGEST', 'REVIEW'],
                'datasets': ['READ', 'OWNER'],
                'groups': ['LIST'],
                'projects': ['LIST'],
                'raw': ['READ', 'WRITE', 'LIST'],
                'robotics': ['READ', 'CREATE', 'UPDATE', 'DELETE'],
                'sessions': ['LIST', 'CREATE'],
                'threed': ['READ', 'CREATE', 'UPDATE', 'DELETE'],
                'documentFeedback': ['READ', 'CREATE', 'DELETE'],
                '_': ['READ', 'WRITE']
            }
        },
        {
            'name': 'READ',
            'description': '',
            'action_mapping': {'raw': ['READ', 'LIST'], 'groups': ['LIST'], 'projects': ['LIST'], 'sessions': ['LIST'], '_': ['READ']}
        },
        {
            'name': 'GOVERNANCE',
            'description': '',
            'action_mapping': {
                'datasets': ['READ', 'WRITE', 'OWNER'],
                'groups': ['LIST', 'READ', 'CREATE', 'UPDATE', 'DELETE'],
                'securityCategories': ['MEMBEROF', 'LIST', 'CREATE', 'DELETE'],
                'projects': ['READ', 'UPDATE', 'LIST']
            }
        }
    ],
    'acl_sets': [
        {
            'name': 'with-scoping',
            'description': '',
            'compose': [],
            'exclude': [],
            'explicit': [
                'assets',
                'dataModelInstances',
                'dataModels',
                'datasets',
                'events',
                'extractionConfigs',
                'extractionPipelines',
                'extractionRuns',
                'files',
                'groups',
                'labels',
                'raw',
                'relationships',
                'robotics',
                'sequences',
                'templateGroups',
                'templateInstances',
                'threed',
                'timeSeries',
                'transformations'
            ]
        },
        {
            'name': 'without-scoping',
            'description': '',
            'compose': [],
            'exclude': [],
            'explicit': [
                'annotations',
                'digitalTwin',
                'entitymatching',
                'functions',
                'geospatial',
                'geospatialCrs',
                'projects',
                'seismic',
                'sessions',
                'timeSeriesSubscriptions',
                'types',
                'wells',
                'documentFeedback',
                'documentPipelines',
                'monitoringTasks',
                'notifications',
                'workflowOrchestration'
            ]
        },
        {'name': 'user', 'description': '', 'compose': ['with-scoping', 'without-scoping'], 'exclude': [], 'explicit': []},
        {'name': 'governance', 'description': '', 'compose': [], 'exclude': [], 'explicit': ['datasets', 'groups', 'projects', 'securityCategories']}
    ],
    'scope_sets': [
        {'name': 'unscoped', 'description': '', 'all_scope': True, 'compose': [], 'exclude': [], 'explicit': []},
        {
            'name': 'canvas',
            'description': '',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {
                'rawdbs': [],
                'spaces': [
                    {'name': 'cdf_apps_shared'},
                    {'name': 'cdf_industrial_canvas'},
                    {'name': 'IndustrialCanvasInstanceSpace'},
                    {'name': 'CommentInstanceSpace'}
                ],
                'datasets': []
            }
        },
        {
            'name': 'infield-common-model',
            'description': 'required by guest, normal and admin',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {
                'rawdbs': [],
                'spaces': [{'name': 'APM_Config'}, {'name': 'cdf_apm'}, {'name': 'cdf_infield'}, {'name': 'cdf_core'}, {'name': 'cdf_apps_shared'}],
                'datasets': []
            }
        },
        {
            'name': 'infield-common-instances',
            'description': 'required by guest, normal and admin',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [], 'spaces': [{'name': 'APM_Config'}, {'name': 'cdf_apm'}, {'name': 'cognite_app_data'}], 'datasets': []}
        },
        {
            'name': 'infield-guest-instances',
            'description': 'required by guest',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [], 'spaces': [{'name': 'cognite_app_data'}], 'datasets': []}
        },
        {
            'name': 'infield-admin-instances',
            'description': 'required by admin',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [], 'spaces': [{'name': 'APM_Config'}], 'datasets': []}
        },
        {
            'name': 'infield-rb-location-instances',
            'description': 'custom scope for rb:?? or in:??',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [], 'spaces': [{'name': 'dp-006-rb-mongstad-spc'}, {'name': 'dp-007-rb-sture-spc'}], 'datasets': []}
        },
        {
            'name': 'src-all',
            'description': '',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [{'name': 'src:all:db'}], 'spaces': [{'name': 'src-all-spc'}], 'datasets': [{'name': 'src:all'}]}
        },
        {
            'name': 'in-all',
            'description': '',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {'rawdbs': [{'name': 'in:all:db'}], 'spaces': [{'name': 'in-all-spc'}], 'datasets': [{'name': 'in:all'}]}
        },
        {
            'name': 'in-001',
            'description': '',
            'all_scope': False,
            'compose': ['src-all', 'in-all'],
            'exclude': [],
            'explicit': {
                'rawdbs': [
                    {'name': 'src:001:sap:db'},
                    {'name': 'src:001:sap:db:state'},
                    {'name': 'src:002:weather:db'},
                    {'name': 'src:003:openint:db'},
                    {'name': 'src:004:test:db'}
                ],
                'spaces': [{'name': 'src-001-sap-spc'}, {'name': 'src-002-weather-spc'}, {'name': 'src-003-openint-spc'}, {'name': 'src-004-test-spc'}],
                'datasets': [{'name': 'src:001:sap'}, {'name': 'src:002:weather'}, {'name': 'src:003:openint'}, {'name': 'src:004:test'}]
            }
        },
        {
            'name': 'uc-001',
            'description': '',
            'all_scope': False,
            'compose': [],
            'exclude': [],
            'explicit': {
                'rawdbs': [{'name': 'uc:001:vessel:db'}, {'name': 'uc:001:vessel:db:state'}],
                'spaces': [{'name': 'uc-001-vessel-spc'}],
                'datasets': [{'name': 'uc:001:vessel'}]
            }
        }
    ],
    'capability_sets': [
        {
            'name': 'governance',
            'description': '',
            'compose': [],
            'exclude': [],
            'capabilities': [{'acls': ['governance'], 'scopes': ['unscoped'], 'actions': ['GOVERNANCE']}]
        },
        {
            'name': 'canvas',
            'description': '',
            'compose': [],
            'exclude': [],
            'capabilities': [
                {'acls': ['dataModels'], 'scopes': ['canvas'], 'actions': ['READ']},
                {'acls': ['dataModelInstances'], 'scopes': ['canvas'], 'actions': ['OWNER']}
            ]
        },
        {
            'name': 'infield-common',
            'description': '',
            'compose': [],
            'exclude': [],
            'capabilities': [
                {'acls': ['dataModels'], 'scopes': ['infield-common-model'], 'actions': ['READ']},
                {'acls': ['dataModelInstances'], 'scopes': ['infield-common-instances'], 'actions': ['READ']},
                {'acls': ['dataModelInstances'], 'scopes': ['infield-guest-instances'], 'actions': ['OWNER']}
            ]
        },
        {
            'name': 'infield-admin',
            'description': 'additional write permission to admin instance space',
            'compose': ['infield-common'],
            'exclude': [],
            'capabilities': [{'acls': ['dataModelInstances'], 'scopes': ['infield-admin-instances'], 'actions': ['OWNER']}]
        },
        {
            'name': 'infield-rb-user',
            'description': '',
            'compose': ['infield-common'],
            'exclude': [],
            'capabilities': [{'acls': ['dataModelInstances'], 'scopes': ['infield-rb-location-instances'], 'actions': ['OWNER']}]
        },
        {
            'name': 'in-001-owner',
            'description': '',
            'compose': [],
            'exclude': [],
            'capabilities': [
                {'acls': ['governance'], 'scopes': ['in-001'], 'actions': ['READ']},
                {'acls': ['user'], 'scopes': ['in-001'], 'actions': ['OWNER']}
            ]
        },
        {
            'name': 'uc-001-owner',
            'description': '',
            'compose': [],
            'exclude': [],
            'capabilities': [
                {'acls': ['governance'], 'scopes': ['uc-001'], 'actions': ['READ']},
                {'acls': ['user'], 'scopes': ['uc-001'], 'actions': ['OWNER']}
            ]
        }
    ]
}
```