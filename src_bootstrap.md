# Table of Contents

* [bootstrap](#bootstrap)
* [bootstrap.\_\_main\_\_](#bootstrap.__main__)
* [bootstrap.app\_exceptions](#bootstrap.app_exceptions)
  * [BootstrapConfigError](#bootstrap.app_exceptions.BootstrapConfigError)
  * [BootstrapValidationError](#bootstrap.app_exceptions.BootstrapValidationError)
* [bootstrap.app\_container](#bootstrap.app_container)
  * [init\_container](#bootstrap.app_container.init_container)
  * [get\_patched\_cognite\_client](#bootstrap.app_container.get_patched_cognite_client)
  * [DiagramCommandContainer](#bootstrap.app_container.DiagramCommandContainer)
  * [DeployCommandContainer](#bootstrap.app_container.DeployCommandContainer)
* [bootstrap.app\_cache](#bootstrap.app_cache)
  * [CogniteResourceCache](#bootstrap.app_cache.CogniteResourceCache)
    * [RESOURCE\_SELECTOR\_MAPPING](#bootstrap.app_cache.CogniteResourceCache.RESOURCE_SELECTOR_MAPPING)
    * [\_\_str\_\_](#bootstrap.app_cache.CogniteResourceCache.__str__)
    * [dump](#bootstrap.app_cache.CogniteResourceCache.dump)
    * [get\_names](#bootstrap.app_cache.CogniteResourceCache.get_names)
    * [create](#bootstrap.app_cache.CogniteResourceCache.create)
    * [delete](#bootstrap.app_cache.CogniteResourceCache.delete)
    * [update](#bootstrap.app_cache.CogniteResourceCache.update)
  * [CogniteDeployedCache](#bootstrap.app_cache.CogniteDeployedCache)
* [bootstrap.common.cognite\_client](#bootstrap.common.cognite_client)
  * [get\_cognite\_client](#bootstrap.common.cognite_client.get_cognite_client)
* [bootstrap.common.base\_model](#bootstrap.common.base_model)
  * [to\_hyphen\_case](#bootstrap.common.base_model.to_hyphen_case)
* [bootstrap.common](#bootstrap.common)
* [bootstrap.app\_config](#bootstrap.app_config)
  * [BootstrapCoreConfig](#bootstrap.app_config.BootstrapCoreConfig)
    * [get\_idp\_cdf\_mapping\_for\_group](#bootstrap.app_config.BootstrapCoreConfig.get_idp_cdf_mapping_for_group)
  * [BootstrapDeleteConfig](#bootstrap.app_config.BootstrapDeleteConfig)
* [bootstrap.commands.prepare](#bootstrap.commands.prepare)
* [bootstrap.commands.deploy](#bootstrap.commands.deploy)
* [bootstrap.commands.base](#bootstrap.commands.base)
  * [CommandBase](#bootstrap.commands.base.CommandBase)
    * [validate\_config\_length\_limits](#bootstrap.commands.base.CommandBase.validate_config_length_limits)
    * [validate\_config\_shared\_access](#bootstrap.commands.base.CommandBase.validate_config_shared_access)
    * [generate\_default\_action](#bootstrap.commands.base.CommandBase.generate_default_action)
    * [generate\_group\_name\_and\_capabilities](#bootstrap.commands.base.CommandBase.generate_group_name_and_capabilities)
    * [get\_group\_ids\_by\_name](#bootstrap.commands.base.CommandBase.get_group_ids_by_name)
    * [create\_group](#bootstrap.commands.base.CommandBase.create_group)
* [bootstrap.commands.diagram](#bootstrap.commands.diagram)
  * [CommandDiagram](#bootstrap.commands.diagram.CommandDiagram)
    * [command](#bootstrap.commands.diagram.CommandDiagram.command)
* [bootstrap.commands.delete](#bootstrap.commands.delete)
* [bootstrap.commands](#bootstrap.commands)
* [bootstrap.commands.diagram\_utils.mermaid](#bootstrap.commands.diagram_utils.mermaid)
  * [GraphRegistry](#bootstrap.commands.diagram_utils.mermaid.GraphRegistry)
* [bootstrap.commands.diagram\_utils](#bootstrap.commands.diagram_utils)

<a id="bootstrap"></a>

# bootstrap

<a id="bootstrap.__main__"></a>

# bootstrap.\_\_main\_\_

<a id="bootstrap.app_exceptions"></a>

# bootstrap.app\_exceptions

<a id="bootstrap.app_exceptions.BootstrapConfigError"></a>

## BootstrapConfigError Objects

```python
class BootstrapConfigError(Exception)
```

Exception raised for config parser

**Attributes**:

- `message` - explanation of the error

<a id="bootstrap.app_exceptions.BootstrapValidationError"></a>

## BootstrapValidationError Objects

```python
class BootstrapValidationError(Exception)
```

Exception raised for config validation

**Attributes**:

- `message` - explanation of the error

<a id="bootstrap.app_container"></a>

# bootstrap.app\_container

<a id="bootstrap.app_container.init_container"></a>

#### init\_container

```python
def init_container(container_cls: containers.Container,
                   config_path: str | Path = "/etc/f25e/config.yaml",
                   dotenv_path: str | Path = None)
```

Spinning up container and

**Arguments**:

- `container_cls` _containers.Container_ - support different
- `config_path` _str | Path, optional_ - _description_. Defaults to "/etc/f25e/config.yaml".
- `dotenv_path` _str | Path, optional_ - _description_. Defaults to None.


**Returns**:

- `_type_` - _description_

<a id="bootstrap.app_container.get_patched_cognite_client"></a>

#### get\_patched\_cognite\_client

```python
def get_patched_cognite_client(cognite_config: CogniteConfig) -> CogniteClient
```

Get an authenticated CogniteClient for the given project and user

**Returns**:

- `CogniteClient` - The authenticated CogniteClient

<a id="bootstrap.app_container.DiagramCommandContainer"></a>

## DiagramCommandContainer Objects

```python
class DiagramCommandContainer(BaseContainer)
```

Container w/o 'cognite_client'

**Arguments**:

- `BaseContainer` __type__ - _description_

<a id="bootstrap.app_container.DeployCommandContainer"></a>

## DeployCommandContainer Objects

```python
class DeployCommandContainer(CogniteContainer)
```

Container providing 'cognite_client' and 'bootstrap'

**Arguments**:

- `CogniteContainer` __type__ - _description_

<a id="bootstrap.app_cache"></a>

# bootstrap.app\_cache

<a id="bootstrap.app_cache.CogniteResourceCache"></a>

## CogniteResourceCache Objects

```python
class CogniteResourceCache(UserList)
```

Implement own CogniteResourceList class
To support generic code for Group, DataSet, Space and Database
Which support simple insert, update or remove (which CogniteResourceList lacks)

<a id="bootstrap.app_cache.CogniteResourceCache.RESOURCE_SELECTOR_MAPPING"></a>

#### RESOURCE\_SELECTOR\_MAPPING

noqa

<a id="bootstrap.app_cache.CogniteResourceCache.__str__"></a>

#### \_\_str\_\_

```python
def __str__() -> str
```

From CogniteResourceList

**Returns**:

- `_type_` - _description_

<a id="bootstrap.app_cache.CogniteResourceCache.dump"></a>

#### dump

```python
def dump(camel_case: bool = False) -> List[Dict[str, Any]]
```

Dump the instance into a json serializable Python data type.

**Arguments**:

- `camel_case` _bool_ - Use camelCase for attribute names. Defaults to False.

**Returns**:

  List[Dict[str, Any]]: A list of dicts representing the instance.

<a id="bootstrap.app_cache.CogniteResourceCache.get_names"></a>

#### get\_names

```python
def get_names() -> List[str]
```

Convenience function to get list of names

**Returns**:

- `List[str]` - _description_

<a id="bootstrap.app_cache.CogniteResourceCache.create"></a>

#### create

```python
def create(
        resources: Union[CogniteResource, CogniteResourceList, List]) -> None
```

map 'mode' to internal update function ('_' prefixed)

**Arguments**:

- `mode` _CacheUpdateMode_ - _description_
- `resources` _CogniteResourceList_ - _description_

<a id="bootstrap.app_cache.CogniteResourceCache.delete"></a>

#### delete

```python
def delete(
        resources: Union[CogniteResource, CogniteResourceList, List]) -> None
```

Find existing resource and replace it
a) delete
b) call create

**Arguments**:

- `resources` _CogniteResourceList_ - _description_

<a id="bootstrap.app_cache.CogniteResourceCache.update"></a>

#### update

```python
def update(
        resources: Union[CogniteResource, CogniteResourceList, List]) -> None
```

Find existing resource and replace it
a) delete
b) call create

**Arguments**:

- `resources` _CogniteResourceList_ - _description_

<a id="bootstrap.app_cache.CogniteDeployedCache"></a>

## CogniteDeployedCache Objects

```python
class CogniteDeployedCache()
```

Load CDF groups, datasets and RAW DBs as pd.DataFrames
and store them in 'self.deployed' dictionary.

<a id="bootstrap.common.cognite_client"></a>

# bootstrap.common.cognite\_client

<a id="bootstrap.common.cognite_client.get_cognite_client"></a>

#### get\_cognite\_client

```python
def get_cognite_client(cognite_config: CogniteConfig) -> CogniteClient
```

Get an authenticated CogniteClient for the given project and user

**Returns**:

- `CogniteClient` - The authenticated CogniteClient

<a id="bootstrap.common.base_model"></a>

# bootstrap.common.base\_model

<a id="bootstrap.common.base_model.to_hyphen_case"></a>

#### to\_hyphen\_case

```python
def to_hyphen_case(value: str) -> str
```

Creates alias names from Python compatible snake_case '_' to yaml typical kebap-style ('-')
# https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/

**Arguments**:

- `value` _str_ - the value to generate an alias for


**Returns**:

- `str` - alias in hyphen-style

<a id="bootstrap.common"></a>

# bootstrap.common

<a id="bootstrap.app_config"></a>

# bootstrap.app\_config

<a id="bootstrap.app_config.BootstrapCoreConfig"></a>

## BootstrapCoreConfig Objects

```python
class BootstrapCoreConfig(Model)
```

Configuration parameters for CDF Project Bootstrap,
deploy(create), prepare, diagram mode

<a id="bootstrap.app_config.BootstrapCoreConfig.get_idp_cdf_mapping_for_group"></a>

#### get\_idp\_cdf\_mapping\_for\_group

```python
def get_idp_cdf_mapping_for_group(cdf_project, cdf_group) -> IdpCdfMapping
```

Return the IdpCdfMapping for the given cdf_project and cdf_group (two nested-loops with filter)

<a id="bootstrap.app_config.BootstrapDeleteConfig"></a>

## BootstrapDeleteConfig Objects

```python
class BootstrapDeleteConfig(Model)
```

Configuration parameters for CDF Project Bootstrap 'delete' command

<a id="bootstrap.commands.prepare"></a>

# bootstrap.commands.prepare

<a id="bootstrap.commands.deploy"></a>

# bootstrap.commands.deploy

<a id="bootstrap.commands.base"></a>

# bootstrap.commands.base

<a id="bootstrap.commands.base.CommandBase"></a>

## CommandBase Objects

```python
class CommandBase()
```

<a id="bootstrap.commands.base.CommandBase.validate_config_length_limits"></a>

#### validate\_config\_length\_limits

```python
def validate_config_length_limits()
```

Validate features in config

<a id="bootstrap.commands.base.CommandBase.validate_config_shared_access"></a>

#### validate\_config\_shared\_access

```python
def validate_config_shared_access()
```

Check shared-access configuration, that all node-names exist

**Returns**:

- `self` - allows validation chaining

<a id="bootstrap.commands.base.CommandBase.generate_default_action"></a>

#### generate\_default\_action

```python
def generate_default_action(action: RoleType, acl_type: str) -> List[str]
```

bootstrap-cli supports two roles: READ, OWNER (called action as parameter)
Each acl and role resolves to a list of default or custom actions.
- Default actions are hard-coded as ["READ", "WRITE"] or ["READ"]
- Custom actions are configured 'ActionDimensions'

**Arguments**:

- `action` _RoleType_ - a supported bootstrap-role, representing a group of actions
- `acl_type` _str_ - an acl from 'AclDefaultTypes'


**Returns**:

- `List[str]` - list of action

<a id="bootstrap.commands.base.CommandBase.generate_group_name_and_capabilities"></a>

#### generate\_group\_name\_and\_capabilities

```python
def generate_group_name_and_capabilities(
        action: str = None,
        ns_name: str = None,
        node_name: str = None,
        root_account: str = None) -> Tuple[str, List[Dict[str, Any]]]
```

Create the group-name and its capabilities.
The function supports following levels expressed by parameter combinations:
- core: {action} + {ns_name} + {node_name}
- namespace: {action} + {ns_name}
- top-level: {action}
- root: {root_account}

**Arguments**:

  action (str, optional):
  One of the ActionDimensions [RoleType.READ, RoleType.OWNER].
  Defaults to None.
  ns_name (str, optional):
  Namespace like "src" or "uc".
  Defaults to None.
  node_name (str, optional):
  Core group like "src:001:sap" or "uc:003:demand".
  Defaults to None.
  root_account (str, optional):
  Name of the root-account.
  Defaults to None.


**Returns**:

  Tuple[str, List[Dict[str, Any]]]: group-name and list of capabilities

<a id="bootstrap.commands.base.CommandBase.get_group_ids_by_name"></a>

#### get\_group\_ids\_by\_name

```python
def get_group_ids_by_name(group_name: str) -> List[int]
```

Lookup if CDF group name exists (could be more than one!)
and return list of all CDF group IDs

**Arguments**:

- `group_name` _str_ - CDF group name to check


**Returns**:

- `List[int]` - of CDF group IDs

<a id="bootstrap.commands.base.CommandBase.create_group"></a>

#### create\_group

```python
def create_group(group_name: str,
                 group_capabilities: Dict[str, Any] = None,
                 idp_mapping: Tuple[str] = None) -> Group
```

Creating a CDF group
- with upsert support the same way Fusion updates CDF groups
if a group with the same name exists:
1. a new group with the same name will be created
2. then the old group will be deleted (by its 'id')
- with support of explicit given aad-mapping or internal lookup from config

**Arguments**:

- `group_name` _str_ - name of the CDF group (always prefixed with GROUP_NAME_PREFIX)
- `group_capabilities` _List[Dict[str, Any]], optional_ - Defining the CDF group capabilities.
  aad_mapping (Tuple[str, str], optional):
  Tuple of ({AAD SourceID}, {AAD SourceName})
  to link the CDF group to


**Returns**:

- `Group` - the new created CDF group

<a id="bootstrap.commands.diagram"></a>

# bootstrap.commands.diagram

<a id="bootstrap.commands.diagram.CommandDiagram"></a>

## CommandDiagram Objects

```python
class CommandDiagram(CommandBase)
```

<a id="bootstrap.commands.diagram.CommandDiagram.command"></a>

#### command

```python
def command(to_markdown: YesNoType = YesNoType.no,
            with_raw_capability: YesNoType = YesNoType.yes,
            cdf_project: str = None) -> None
```

Diagram mode used to document the given configuration as a Mermaid diagram.

**Arguments**:

  to_markdown (YesNoType, optional):
  - Encapsulate Mermaid diagram in Markdown syntax.
  - Defaults to 'YesNoType.no'.
  with_raw_capability (YesNoType, optional):
  - Create RAW DBs and 'rawAcl' capability. Defaults to 'YesNoType.tes'.
  cdf_project (str, optional):
  - Provide the CDF Project to use for the diagram 'idp-cdf-mappings'.


**Example**:

  # requires a 'cognite' configuration section
  ➟  poetry run bootstrap-cli diagram configs/config-deploy-example-v2.yml | clip.exe
  # precedence over 'cognite.project' which CDF Project to diagram 'bootstrap.idp-cdf-mappings'
  # making a 'cognite' section optional
  ➟  poetry run bootstrap-cli diagram --cdf-project shiny-dev configs/config-deploy-example-v2.yml | clip.exe
  # precedence over configuration 'bootstrap.features.with-raw-capability'
  ➟  poetry run bootstrap-cli diagram --with-raw-capability no --cdf-project shiny-prod configs/config-deploy-example-v2.yml

<a id="bootstrap.commands.delete"></a>

# bootstrap.commands.delete

<a id="bootstrap.commands"></a>

# bootstrap.commands

<a id="bootstrap.commands.diagram_utils.mermaid"></a>

# bootstrap.commands.diagram\_utils.mermaid

<a id="bootstrap.commands.diagram_utils.mermaid.GraphRegistry"></a>

## GraphRegistry Objects

```python
class GraphRegistry()
```

A graph reqistry is
* a list of elements and edges to render (representing the "graph")
* provides a registry for lookup of already created subgraphs by name for reuse ("get_or_create")
* supports printing the graph in a mermaid-compatible format

<a id="bootstrap.commands.diagram_utils"></a>

# bootstrap.commands.diagram\_utils
