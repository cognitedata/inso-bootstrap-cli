#          888                                          888
#          888                                          888
#          888                                          888
#  .d8888b 88888b.   8888b.  88888b.   .d88b.   .d88b.  888  .d88b.   .d88b.
# d88P"    888 "88b     "88b 888 "88b d88P"88b d8P  Y8b 888 d88""88b d88P"88b
# 888      888  888 .d888888 888  888 888  888 88888888 888 888  888 888  888
# Y88b.    888  888 888  888 888  888 Y88b 888 Y8b.     888 Y88..88P Y88b 888
#  "Y8888P 888  888 "Y888888 888  888  "Y88888  "Y8888  888  "Y88P"   "Y88888
#                                          888                            888
#                                     Y8b d88P                       Y8b d88P
#                                      "Y88P"                         "Y88P"
#
# 210504 mh:
#  * Adding support for minimum groups and project capabilities for read and owner groups
#  * Exception handling for root-groups to avoid duplicate groups and projects capabilities
# 210610 mh:
#  * Adding RAW DBs and datasets for groups {env}:allprojects:{owner/read} and {env}:{group}:allprojects:{owner/read}
#  * Adding functionality for updating dataset details (external id, description, etc) based on the config.yml
# 210910 pa:
#  * extended acl_default_types by labels, relationships, functions
#  * removed labels from acl_admin_types
#  * functions don't have dataset scope
# 211013 pa:
#  * renamed "adfs" to "aad" terminology => aad_mappings
#  * for AAD 'root:client' and 'root:user' can be merged into 'root'
# 211014 pa:
#  * adding new capabilities
#       extractionpipelinesAcl
#       extractionrunsAcl
# 211108 pa:
#  * adding new capabilities
#       entitymatchingAcl
#  * refactor list of acl types which only support "all" scope
#       acl_all_scope_only_types
#  * support "labels" for non admin groups
# 211110 pa:
#  * adding new capabilities
#       sessionsAcl
# 220202 pa:
#  * adding new capabilities
#       typesAcl
# 220216 pa:
#  * adding 'generate_special_groups()' to handle
#    'extractors' and 'transformations' and their 'aad_mappings'
#    * configurable through `deploy --with-special-groups=[yes|no]` parameter
#  * adding new capabilities:
#       transformationsAcl (replacing the need for magic "transformations" CDF group)
# 220404 pa:
#  * v1.4.0 limited datasets for 'owner' that they cannot edit or create datasets
#     * removed `datasets:write` capability
#     * moved that capability to action_dimensions['admin']
# 220405 sd:
#  * v1.5.0 added dry-run mode as global parameter for all commands
# 220405 pa:
#  * v1.6.0
#  * removed 'transformation' acl from 'acl_all_scope_only_types'
#     as it now supports dataset scopes too!
#  * refactor variable names to match the new documentation
#     1. group_types_dimensions > group_bootstrap_hierarchy
#     2. group_type > ns_name (namespace: src, ca, uc)
#     3. group_prefix > node_name (src:001:sap)
# 220406 pa/sd:
#  * v1.7.0
#  * added 'diagram' command which creates a Mermaid (diagram as code) output
# 220406 pa:
#  * v1.7.1
#  * started to use '# fmt:skip' to save intended multiline formatted and indented code
#    from black auto-format
# 220420 pa:
#  * v.1.9.2
#  * fixed Poetry on Windows issues
# 220422 pa:
#  * v1.10.0
#  *  issue #28 possibility to skip creation of RAW DBs
#  * added '--with-raw-capability' parameter for 'deploy' and 'diagram' commands
# 220424 pa:
#  * introduced CommandMode enums to support more detailed BootstrapCore initialization
#  * started with validation-functions ('validate_config_is_cdf_project_in_mappings')
#  * for 'diagram' command
#    - made 'cognite' section optional
#    - added support for parameter '--cdf-project' to explicit diagram a specific CDF Project
#    - Added cdf-project name to diagram "IdP groups for CDF: <>" subgraph title
#    - renamed mermaid properties from 'name/short' to 'id_name/display'
#  * documented config-deploy-example-v2.yml
# 220511 pa: v2.0.0 release :)
# 220728 pa: v2.0.2 release with replacing time.sleep() statements (which could fail to reload CDF resources)
#     through active caching of CDF resource changes
#     * the 'self.deployed' is now of type 'CogniteDeployedCache' with support to create, update or delete cache entries
#     Potential problem fixed with DRY-RUN and 'delete' command
#     * enhanced dry-run logging
#     Removed chunks from dataset creation (already covered by SDK)


#
# TODO:
#
# 220728 pa: validation step if all shared groups are covered by config

import json
import logging
from collections import UserList
from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union

import click
import yaml
from click import Context
from cognite.client import utils
from cognite.client.data_classes import Database, DatabaseList, DataSet, DataSetList, DataSetUpdate, Group, GroupList
from cognite.client.data_classes._base import CogniteResource, CogniteResourceList
from cognite.extractorutils.configtools import CogniteClient
from dotenv import load_dotenv

# cli internal
from incubator.bootstrap_cli import __version__
from incubator.bootstrap_cli.configuration import (
    BootstrapConfigError,
    BootstrapDeleteConfig,
    BootstrapDeployConfig,
    BootstrapValidationError,
    CommandMode,
    SharedAccess,
    YesNoType,
)
from incubator.bootstrap_cli.mermaid_generator.mermaid import (
    AssymetricNode,
    DottedEdge,
    Edge,
    GraphRegistry,
    Node,
    RoundedNode,
    SubroutineNode,
    TrapezNode,
)

# '''
#           888          888               888                               .d888 d8b
#           888          888               888                              d88P"  Y8P
#           888          888               888                              888
#   .d88b.  888  .d88b.  88888b.   8888b.  888     .d8888b .d88b.  88888b.  888888 888  .d88b.  .d8888b
#  d88P"88b 888 d88""88b 888 "88b     "88b 888    d88P"   d88""88b 888 "88b 888    888 d88P"88b 88K
#  888  888 888 888  888 888  888 .d888888 888    888     888  888 888  888 888    888 888  888 "Y8888b.
#  Y88b 888 888 Y88..88P 888 d88P 888  888 888    Y88b.   Y88..88P 888  888 888    888 Y88b 888      X88
#   "Y88888 888  "Y88P"  88888P"  "Y888888 888     "Y8888P "Y88P"  888  888 888    888  "Y88888  88888P'
#       888                                                                                 888
#  Y8b d88P                                                                            Y8b d88P
#   "Y88P"                                                                              "Y88P"
# '''
_logger = logging.getLogger(__name__)

# because within f'' strings no backslash-character is allowed
NEWLINE = "\n"

# capabilities (acl) which only support  scope: {"all":{}}
acl_all_scope_only_types = set(
    [
        "projects",
        "sessions",
        "functions",
        "entitymatching",
        "types",
        "threed",
    ]
)
# lookup of non-default actions per capability (acl) and role (owner/read/admin)
action_dimensions = {
    # owner datasets might only need READ and OWNER
    "owner": {  # else ["READ","WRITE"]
        "raw": ["READ", "WRITE", "LIST"],
        "datasets": ["READ", "OWNER"],
        "groups": ["LIST"],
        "projects": ["LIST"],
        "sessions": ["LIST", "CREATE"],
        "threed": ["READ", "CREATE", "UPDATE", "DELETE"],
    },
    "read": {  # else ["READ"]
        "raw": ["READ", "LIST"],
        "groups": ["LIST"],
        "projects": ["LIST"],
        "sessions": ["LIST"],
    },
    "admin": {
        "datasets": ["READ", "WRITE", "OWNER"],
        "groups": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"],
        "projects": ["READ", "UPDATE", "LIST"],
    },
}

#
# GENERIC configurations
# extend when new capability (acl) is available
# check if action_dimensions must be extended with non-default capabilities:
#   which are owner: ["READ","WRITE"]
#   and read: ["READ"])
#
acl_default_types = [
    "assets",
    "datasets",
    "entitymatching",
    "events",
    "extractionPipelines",
    "extractionRuns",
    "files",
    "functions",
    "groups",
    "labels",
    "projects",
    "raw",
    "relationships",
    "sequences",
    "sessions",
    "timeSeries",
    "transformations",
    "types",
    "threed",
]

# give precedence when merging over acl_default_types
acl_admin_types = list(action_dimensions["admin"].keys())


class CacheUpdateMode(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class CogniteResourceCache(UserList):
    """Implement own CogniteResourceList class
    To support generic code for Group, DataSet and Database
    Which support simple insert, update or remove (which CogniteResourceList lacks)
    """

    # not all CDF resources support 'id' for selection, so this is the dynamic lookup for
    RESOURCE_SELECTOR_MAPPING = {DataSet: "id", Group: "id", Database: "name"}  # noqa

    def __init__(
        self, RESOURCE: Union[Group, Database, DataSet], resources: Union[CogniteResource, CogniteResourceList]
    ) -> None:
        self.RESOURCE: Union[Group, Database, DataSet] = RESOURCE
        self.SELECTOR_FIELD = CogniteResourceCache.RESOURCE_SELECTOR_MAPPING[RESOURCE]

        _logger.info(f"Init Resource Cache {RESOURCE=} with SELECTOR_FIELD='{self.SELECTOR_FIELD}'")

        # a) unpack ResourceList to simple list
        # b) is single element, pack it in list
        self.data = [r for r in resources] if isinstance(resources, CogniteResourceList) else [resources]

    def __str__(self) -> str:
        """From CogniteResourceList

        Returns:
            _type_: _description_
        """
        item = utils._time.convert_time_attributes_to_datetime(self.dump())
        return json.dumps(item, default=utils._auxiliary.json_dump_default, indent=4)

    def dump(self, camel_case: bool = False) -> List[Dict[str, Any]]:
        """Dump the instance into a json serializable Python data type.
        Args:
            camel_case (bool): Use camelCase for attribute names. Defaults to False.
        Returns:
            List[Dict[str, Any]]: A list of dicts representing the instance.
        """
        return [resource.dump(camel_case) for resource in self.data]

    def get_names(self) -> List[str]:
        """Convenience function to get list of names

        Returns:
            List[str]: _description_
        """
        return [(resource.name or "") for resource in self.data]

    def select(self, values):
        return [c for c in self.data if getattr(c, self.SELECTOR_FIELD) in values]

    def create(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """map 'mode' to internal update function ('_' prefixed)

        Args:
            mode (CacheUpdateMode): _description_
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]
        self.data.extend([r for r in resources])

    def delete(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """Find existing resource and replace it
        a) delete
        b) call create

        Args:
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]

        # delete if exists
        matching_in_cache = self.select(values=[getattr(r, self.SELECTOR_FIELD) for r in resources])
        [self.data.remove(m) for m in matching_in_cache]

    def update(self, resources: Union[CogniteResource, CogniteResourceList, List]) -> None:
        """Find existing resource and replace it
        a) delete
        b) call create

        Args:
            resources (CogniteResourceList): _description_
        """
        # handle single-element, with CogniteResourceList and List are Iterable
        resources = resources if isinstance(resources, Iterable) else [resources]

        # delete if exists
        self.delete(resources)
        # create
        self.create(resources)


class CogniteDeployedCache:
    """Load CDF groups, datasets and RAW DBs as pd.DataFrames
    and store them in 'self.deployed' dictionary.
    """

    def __init__(self, client: CogniteClient, groups_only: bool = False):

        """Load CDF groups, datasets and raw databases as CogniteResourceList
        and store them in 'self.deployed' dictionary.

        Args:
            groups_only (bool, optional): Limit to CDF groups only (used by 'prepare' command). Defaults to False.
        """
        NOLIMIT = -1

        self.client: CogniteClient = client
        self.groups: CogniteResourceCache = CogniteResourceCache(
            RESOURCE=Group, resources=self.client.iam.groups.list(all=True)
        )

        if groups_only:
            #
            # early exit
            #
            self.cache = {"groups": self.groups}
            return

        self.datasets: CogniteResourceCache = CogniteResourceCache(
            RESOURCE=DataSet, resources=self.client.data_sets.list(limit=NOLIMIT)
        )
        self.raw_dbs: CogniteResourceCache = CogniteResourceCache(
            RESOURCE=Database, resources=self.client.raw.databases.list(limit=NOLIMIT)
        )

    def log_counts(self):
        _logger.info(
            f"""Deployed CDF Resource counts:
            RAW Dbs({len(self.raw_dbs.get_names())})
            Data Sets({len(self.datasets.get_names())})
            CDF Groups({len(self.groups.get_names())})"""
        )


# '''
#  888888b.                     888             888                              .d8888b.
#  888  "88b                    888             888                             d88P  Y88b
#  888  .88P                    888             888                             888    888
#  8888888K.   .d88b.   .d88b.  888888 .d8888b  888888 888d888 8888b.  88888b.  888         .d88b.  888d888 .d88b.
#  888  "Y88b d88""88b d88""88b 888    88K      888    888P"      "88b 888 "88b 888        d88""88b 888P"  d8P  Y8b
#  888    888 888  888 888  888 888    "Y8888b. 888    888    .d888888 888  888 888    888 888  888 888    88888888
#  888   d88P Y88..88P Y88..88P Y88b.       X88 Y88b.  888    888  888 888 d88P Y88b  d88P Y88..88P 888    Y8b.
#  8888888P"   "Y88P"   "Y88P"   "Y888  88888P'  "Y888 888    "Y888888 88888P"   "Y8888P"   "Y88P"  888     "Y8888
#                                                                      888
#                                                                      888
#                                                                      888
# '''

# type-hint for ExtpipesCore instance response
T_BootstrapCore = TypeVar("T_BootstrapCore", bound="BootstrapCore")


class BootstrapCore:

    # CDF group prefix, i.e. "cdf:", to make bootstrap created CDF groups easy recognizable in Fusion
    GROUP_NAME_PREFIX = ""

    # mandatory for hierarchical-namespace
    AGGREGATED_LEVEL_NAME = ""

    # rawdbs creation support additional variants, for special purposes (like saving statestores)
    # - default-suffix is ':rawdb' with no variant-suffix (represented by "")
    # - additional variant-suffixes can be added like this ["", ":state"]
    RAW_VARIANTS = [""]

    def __init__(self, configpath: str, command: CommandMode):
        if command == CommandMode.DELETE:
            self.config: BootstrapDeleteConfig = BootstrapDeleteConfig.from_yaml(configpath)
            self.delete_or_deprecate: Dict[str, Any] = self.config.delete_or_deprecate
            if not self.config.cognite:
                BootstrapConfigError("'cognite' section required in configuration")
        elif command in (CommandMode.DEPLOY, CommandMode.DIAGRAM, CommandMode.PREPARE):

            self.config: BootstrapDeployConfig = BootstrapDeployConfig.from_yaml(configpath)
            self.bootstrap_config: BootstrapDeployConfig = self.config.bootstrap
            self.idp_cdf_mappings = self.bootstrap_config.idp_cdf_mappings

            # CogniteClient is optional for diagram
            if command != CommandMode.DIAGRAM:
                # mandatory section
                if not self.config.cognite:
                    BootstrapConfigError("'cognite' section required in configuration")

            #
            # load 'bootstrap.features'
            #
            # unpack and process features
            features = self.bootstrap_config.features

            # [OPTIONAL] default: False
            self.with_special_groups: bool = features.with_special_groups
            # [OPTIONAL] default: True
            self.with_raw_capability: bool = features.with_raw_capability

            # [OPTIONAL] default: "allprojects"
            BootstrapCore.AGGREGATED_LEVEL_NAME = features.aggregated_level_name
            # [OPTIONAL] default: "cdf:"
            # support for '' empty string
            BootstrapCore.GROUP_NAME_PREFIX = f"{features.group_prefix}:" if features.group_prefix else ""
            # [OPTIONAL] default: "dataset"
            # support for '' empty string
            BootstrapCore.DATASET_SUFFIX = f":{features.dataset_suffix}" if features.dataset_suffix else ""
            # [OPTIONAL] default: "rawdb"
            # support for '' empty string
            BootstrapCore.RAW_SUFFIX = f":{features.rawdb_suffix}" if features.rawdb_suffix else ""
            # [OPTIONAL] default: ["", ":"state"]
            BootstrapCore.RAW_VARIANTS = [""] + [f":{suffix}" for suffix in features.rawdb_additional_variants]

        # migrating to CogniteDeployedCache
        # self.deployed: Dict[str, Any] = {}
        self.deployed: CogniteDeployedCache = None
        self.all_scope_ctx: Dict[str, Any] = {}
        self.is_dry_run: bool = False
        self.client: CogniteClient = None
        self.cdf_project = None

        # TODO debug
        # print(f"self.config= {self.config}")

        # TODO: support 'logger' section optional, provide default config for logger with console only
        #
        # Logger initialisation
        #
        # make sure the optional folders in logger.file.path exists
        # to avoid: FileNotFoundError: [Errno 2] No such file or directory: '/github/workspace/logs/test-deploy.log'
        if self.config.logger.file:
            (Path.cwd() / self.config.logger.file.path).parent.mkdir(parents=True, exist_ok=True)
        self.config.logger.setup_logging()
        _logger.info(f"Starting CDF Bootstrap configuration for command: <{command}>")

        # debug new features
        if getattr(self, "bootstrap_config", False):
            # TODO: not available for 'delete' but there must be aa smarter solution
            _logger.debug(
                "Features from yaml-config or defaults (can be overridden by cli-parameters!): "
                f"{self.bootstrap_config.features=}"
            )

        #
        # Cognite initialisation (optional for 'diagram')
        #
        if self.config.cognite:
            self.client: CogniteClient = self.config.cognite.get_cognite_client(  # noqa
                client_name="inso-bootstrap-cli", token_custom_args=self.config.token_custom_args
            )
            self.cdf_project = self.client.config.project
            _logger.info(f"Successful connection to CDF client to project: '{self.cdf_project}'")

            # load CDF group, dataset, rawdb config
            if command in (CommandMode.PREPARE, CommandMode.DEPLOY, CommandMode.DELETE):
                self.deployed = CogniteDeployedCache(self.client, groups_only=(command == CommandMode.PREPARE))
                self.deployed.log_counts()

    @staticmethod
    def acl_template(actions, scope):
        return {"actions": actions, "scope": scope}

    @staticmethod
    def get_allprojects_name_template(ns_name=None):
        return f"{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}" if ns_name else BootstrapCore.AGGREGATED_LEVEL_NAME

    @staticmethod
    def get_dataset_name_template():
        return "{node_name}" + BootstrapCore.DATASET_SUFFIX

    @staticmethod
    def get_raw_dbs_name_template():
        return "{node_name}" + BootstrapCore.RAW_SUFFIX + "{raw_variant}"

    @staticmethod
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def validate_config_length_limits(self):
        """
        Validate features in config
        """

        #
        # CHECK 1 (availability)
        #
        if not self.AGGREGATED_LEVEL_NAME:
            raise BootstrapValidationError(
                "Features validation error: 'features.aggregated-level-name' is required, "
                f"but provided as <{self.AGGREGATED_LEVEL_NAME}>"
            )

        #
        # CHECK 2 (length limits)
        #
        # TODO: GROUP_NAME_LENGTH_LIMIT = ??
        RAWDB_NAME_LENGTH_LIMIT = 32
        DATASET_NAME_LENGTH_LIMIT = 50
        DATASET_EXTERNALID_LENGTH_LIMIT = 255

        # create all required scopes to check name lengths
        all_scopes = {
            # generate_target_raw_dbs -> returns a Set[str]
            "raw": self.generate_target_raw_dbs(),  # all raw_dbs
            # generate_target_datasets -> returns a Dict[str, Any]
            "datasets": self.generate_target_datasets(),  # all datasets
        }

        errors = []
        if self.with_raw_capability:
            errors.extend(
                [
                    ("RAW DB", rawdb_name, len(rawdb_name), RAWDB_NAME_LENGTH_LIMIT)
                    for rawdb_name in all_scopes["raw"]
                    if len(rawdb_name) > RAWDB_NAME_LENGTH_LIMIT
                ]
            )
        errors.extend(
            [
                ("DATA SET name", dataset_name, len(dataset_name), DATASET_NAME_LENGTH_LIMIT)
                for dataset_name, dataset_details in all_scopes["datasets"].items()
                if len(dataset_name) > DATASET_NAME_LENGTH_LIMIT
            ]
        )
        errors.extend(
            [
                (
                    "DATA SET external_id",
                    dataset_details["external_id"],
                    len(dataset_name),
                    DATASET_EXTERNALID_LENGTH_LIMIT,
                )
                for dataset_name, dataset_details in all_scopes["datasets"].items()
                if len(dataset_details["external_id"]) > DATASET_EXTERNALID_LENGTH_LIMIT
            ]
        )

        if errors:
            raise BootstrapValidationError(
                "Features validation error(s):\n"
                # RAW DB src:002:weather:rawdbiswaytoolongtofit : len(38) > 32
                f"""{NEWLINE.join(
                    [
                        f'{scope_type} {scope_error} : len({scope_length}) > {max_length}'
                        for (scope_type, scope_error, scope_length, max_length) in errors
                    ])}"""
            )

        # return self for chaining
        return self

    def validate_config_is_cdf_project_in_mappings(self):

        # check if mapping exists for configured cdf-project
        is_cdf_project_in_mappings = self.cdf_project in [mapping.cdf_project for mapping in self.idp_cdf_mappings]
        if not is_cdf_project_in_mappings:
            _logger.warning(f"No 'idp-cdf-mapping' found for CDF Project <{self.cdf_project}>")
            # log or raise?
            # raise ValueError(f'No mapping for CDF project {self.cdf_project}')

        # return self for chaining
        return self

    def generate_default_action(self, action, acl_type):
        return action_dimensions[action].get(acl_type, ["READ", "WRITE"] if action == "owner" else ["READ"])

    def generate_admin_action(self, acl_admin_type):
        return action_dimensions["admin"][acl_admin_type]

    def get_ns_node_shared_access_by_name(self, node_name) -> SharedAccess:
        for ns in self.bootstrap_config.namespaces:
            for ns_node in ns.ns_nodes:
                if node_name == ns_node.node_name:
                    return ns_node.shared_access
        return SharedAccess([], [])

    def get_group_raw_dbs_groupedby_action(self, action, ns_name, node_name=None):
        raw_db_names: Dict[str, Any] = {"owner": [], "read": []}
        if node_name:
            raw_db_names[action].extend(
                # the dataset which belongs directly to this node_name
                [
                    self.get_raw_dbs_name_template().format(node_name=node_name, raw_variant=raw_variant)
                    for raw_variant in BootstrapCore.RAW_VARIANTS
                ]
            )

            # for owner groups add "shared_owner_access" raw_dbs too
            if action == "owner":
                raw_db_names["owner"].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_node.node_name, raw_variant=raw_variant
                        )
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).owner
                        for raw_variant in BootstrapCore.RAW_VARIANTS
                    ]
                )
                raw_db_names["read"].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_node.node_name, raw_variant=raw_variant
                        )
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).read
                        for raw_variant in BootstrapCore.RAW_VARIANTS
                    ]
                )

        else:  # handling the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME}
            raw_db_names[action].extend(
                [
                    self.get_raw_dbs_name_template().format(node_name=ns_node.node_name, raw_variant=raw_variant)
                    for ns in self.bootstrap_config.namespaces
                    if ns.ns_name == ns_name
                    for ns_node in ns.ns_nodes
                    for raw_variant in BootstrapCore.RAW_VARIANTS
                ]
                # adding the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME} rawdbs
                + [  # noqa
                    self.get_raw_dbs_name_template().format(
                        node_name=self.get_allprojects_name_template(ns_name=ns_name), raw_variant=raw_variant
                    )
                    for raw_variant in BootstrapCore.RAW_VARIANTS
                ]
            )
            # only owner-groups support "shared_access" rawdbs
            if action == "owner":
                raw_db_names["owner"].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_access_node.node_name, raw_variant=raw_variant
                        )
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.owner
                        for raw_variant in BootstrapCore.RAW_VARIANTS
                    ]
                )
                raw_db_names["read"].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_access_node.node_name, raw_variant=raw_variant
                        )
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.read
                        for raw_variant in BootstrapCore.RAW_VARIANTS
                    ]
                )

        # returns clear names grouped by action
        return raw_db_names

    def get_group_datasets_groupedby_action(self, action, ns_name, node_name=None):
        dataset_names: Dict[str, Any] = {"owner": [], "read": []}
        # for example fac:001:wasit, uc:002:meg, etc.
        if node_name:
            dataset_names[action].extend(
                # the dataset which belongs directly to this node_name
                [self.get_dataset_name_template().format(node_name=node_name)]
            )

            # for owner groups add "shared_access" datasets too
            if action == "owner":
                dataset_names["owner"].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_node.node_name)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).owner
                    ]
                )
                dataset_names["read"].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_node.node_name)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).read
                    ]
                )
        # for example src, fac, uc, ca
        else:  # handling the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME}
            dataset_names[action].extend(
                [
                    # all datasets for each of the nodes of the given namespace
                    self.get_dataset_name_template().format(node_name=ns_node.node_name)
                    for ns in self.bootstrap_config.namespaces
                    if ns.ns_name == ns_name
                    for ns_node in ns.ns_nodes
                ]
                # adding the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME} dataset
                + [  # noqa
                    self.get_dataset_name_template().format(
                        node_name=self.get_allprojects_name_template(ns_name=ns_name)
                    )
                ]
            )
            # only owner-groups support "shared_access" datasets
            if action == "owner":
                dataset_names["owner"].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_access_node.node_name)
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.owner
                    ]
                )
                dataset_names["read"].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_access_node.node_name)
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.read
                    ]
                )

        # returns clear names
        return dataset_names

    def dataset_names_to_ids(self, dataset_names):
        return [
            # get id for all dataset names
            ds.id
            for ds in self.deployed.datasets
            if ds.name in dataset_names
        ]

    def get_scope_ctx_groupedby_action(self, action, ns_name, node_name=None):
        ds_by_action = self.get_group_datasets_groupedby_action(action, ns_name, node_name)
        rawdbs_by_action = self.get_group_raw_dbs_groupedby_action(action, ns_name, node_name)
        return {
            action: {"raw": rawdbs_by_action[action], "datasets": ds_by_action[action]}
            for action in ["owner", "read"]
        }  # fmt: skip

    def generate_scope(self, acl_type, scope_ctx):
        if acl_type == "raw":
            # { "tableScope": { "dbsToTables": { "foo:db": {}, "bar:db": {} } }
            return {"tableScope": {"dbsToTables": {raw: {} for raw in scope_ctx["raw"]}}}
        elif acl_type == "datasets":
            # { "idScope": { "ids": [ 2695894113527579, 4254268848874387 ] } }
            return {"idScope": {"ids": self.dataset_names_to_ids(scope_ctx["datasets"])}}
        # adding minimum projects and groups scopes for non-root groups
        # TODO: adding documentation link
        elif acl_type in acl_all_scope_only_types:
            return {"all": {}}
        elif acl_type == "groups":
            return {"currentuserscope": {}}
        else:  # like 'assets', 'events', 'files', 'sequences', 'timeSeries', ..
            # { "datasetScope": { "ids": [ 2695894113527579, 4254268848874387 ] } }
            return {"datasetScope": {"ids": self.dataset_names_to_ids(scope_ctx["datasets"])}}

    def generate_group_name_and_capabilities(
        self, action: str = None, ns_name: str = None, node_name: str = None, root_account: str = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Create the group-name and its capabilities.
        The function supports following levels expressed by parameter combinations:
        - core: {action} + {ns_name} + {node_name}
        - namespace: {action} + {ns_name}
        - top-level: {action}
        - root: {root_account}

        Args:
            action (str, optional):
                One of the action_dimensions ["read", "owner"].
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

        Returns:
            Tuple[str, List[Dict[str, Any]]]: group-name and list of capabilities
        """

        capabilities = []

        # detail level like cdf:src:001:public:read
        if action and ns_name and node_name:
            # group for each dedicated group-core id
            group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{node_name}:{action}"

            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action(shared_action, acl_type),
                            scope=self.generate_scope(acl_type, scope_ctx),
                        )
                    }
                )
                for acl_type in acl_default_types
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(action, ns_name, node_name).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx["raw"] and scope_ctx["datasets"]
            ]

        # group-type level like cdf:src:all:read
        elif action and ns_name:
            # 'all' groups on group-type level
            # (access to all datasets/ raw-dbs which belong to this group-type)
            group_name_full_qualified = (
                f"{BootstrapCore.GROUP_NAME_PREFIX}{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}"
            )

            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action(shared_action, acl_type),
                            scope=self.generate_scope(acl_type, scope_ctx),
                        )
                    }
                )
                for acl_type in acl_default_types
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(action, ns_name).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx["raw"] and scope_ctx["datasets"]
            ]

        # top level like cdf:all:read
        elif action:
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            group_name_full_qualified = (
                f"{BootstrapCore.GROUP_NAME_PREFIX}{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}"
            )

            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action(action, acl_type),
                            # scope = { "all": {} }
                            # create scope for all raw_dbs and datasets
                            scope=self.generate_scope(acl_type, self.all_scope_ctx),
                        )
                    }
                )
                for acl_type in acl_default_types
            ]

        # root level like cdf:root
        elif root_account:  # no parameters
            # all (no limits)
            group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{root_account}"
            # all default ACLs
            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action("owner", acl_type),
                            scope={"all": {}},
                        )
                    }
                )
                # skipping admin types from default types to avoid duplicates
                for acl_type in (set(acl_default_types) - set(acl_admin_types))
            ]
            # plus admin ACLs
            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_admin_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_admin_action(acl_admin_type),
                            scope={"all": {}},
                        )
                    }
                )
                for acl_admin_type in acl_admin_types
            ]
        return group_name_full_qualified, capabilities

    def get_group_ids_by_name(self, group_name: str) -> List[int]:
        """Lookup if CDF group name exists (could be more than one!)
        and return list of all CDF group IDs

        Args:
            group_name (str): CDF group name to check

        Returns:
            List[int]: of CDF group IDs
        """
        return [g.id for g in self.deployed.groups if g.name == group_name]

    def create_group(
        self,
        group_name: str,
        group_capabilities: Dict[str, Any] = None,
        idp_mapping: Tuple[str] = None,
    ) -> Group:
        """Creating a CDF group
        - with upsert support the same way Fusion updates CDF groups
          if a group with the same name exists:
              1. a new group with the same name will be created
              2. then the old group will be deleted (by its 'id')
        - with support of explicit given aad-mapping or internal lookup from config

        Args:
            group_name (str): name of the CDF group (always prefixed with GROUP_NAME_PREFIX)
            group_capabilities (List[Dict[str, Any]], optional): Defining the CDF group capabilities.
            aad_mapping (Tuple[str, str], optional):
                Tuple of ({AAD SourceID}, {AAD SourceName})
                to link the CDF group to

        Returns:
            Group: the new created CDF group
        """

        idp_source_id, idp_source_name = None, None
        if idp_mapping:
            # explicit given
            # TODO: change from tuple to dataclass
            if len(idp_mapping) != 2:
                raise ValueError(f"Expected a tuple of length 2, got {idp_mapping=} instead")
            idp_source_id, idp_source_name = idp_mapping
        else:
            # check lookup from provided config
            mapping = self.bootstrap_config.get_idp_cdf_mapping_for_group(
                cdf_project=self.cdf_project, cdf_group=group_name
            )
            # unpack
            idp_source_id, idp_source_name = mapping.idp_source_id, mapping.idp_source_name

        # check if group already exists, if yes it will be deleted after a new one is created
        old_group_ids = self.get_group_ids_by_name(group_name)

        new_group = Group(name=group_name, capabilities=group_capabilities)
        if idp_source_id:
            # inject (both will be pushed through the API call!)
            new_group.source_id = idp_source_id  # 'S-314159-1234'
            new_group.source = idp_source_name  # type: ignore

        # print(f"group_create_object:<{group_create_object}>")
        # overwrite new_group as it now contains id too
        if self.is_dry_run:
            _logger.info(f"Dry run - Creating group with name: <{new_group.name}>")
            _logger.debug(f"Dry run - Creating group details: <{new_group}>")
        else:
            new_group: Union[Group, GroupList] = self.client.iam.groups.create(new_group)
            self.deployed.groups.create(resources=new_group)
            _logger.info(f"  {new_group.name} ({new_group.id}) [idp source: {new_group.source_id}]")

        # if the group name existed before, delete those groups now
        # same upsert approach Fusion is using to update a CDF group: create new with changes => then delete old one
        if old_group_ids:
            if self.is_dry_run:
                _logger.info(f"Dry run - Deleting groups with ids: <{old_group_ids}>")
            else:
                self.client.iam.groups.delete(old_group_ids)
                self.deployed.groups.delete(resources=self.deployed.groups.select(values=old_group_ids))

        return new_group

    def process_group(
        self, action: str = None, ns_name: str = None, node_name: str = None, root_account: str = None
    ) -> Group:
        # to avoid complex upsert logic, all groups will be recreated and then the old ones deleted

        # to be merged with existing code
        # print(f"=== START: action<{action}> | ns_name<{ns_name}> | node_name<{node_name}> ===")

        group_name, group_capabilities = self.generate_group_name_and_capabilities(
            action, ns_name, node_name, root_account
        )

        group: Group = self.create_group(group_name, group_capabilities)
        return group

    def generate_target_datasets(self) -> Dict[str, Any]:
        # list of all targets: autogenerated dataset names
        target_datasets = {
            # dictionary generator
            # dataset_name : {Optional[dataset_description], Optional[dataset_metadata], ..}
            # key:
            (fq_ns_name := self.get_dataset_name_template().format(node_name=ns_node.node_name)):
            # value
            {
                "description": ns_node.description,
                "metadata": ns_node.metadata,
                # if not explicit provided, same template as name
                "external_id": ns_node.external_id or fq_ns_name,
            }
            for ns in self.bootstrap_config.namespaces
            for ns_node in ns.ns_nodes
        }

        # update target datasets to include 'allproject' and '{ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME}' datasets
        target_datasets.update(
            {  # dictionary generator
                # key:
                self.get_dataset_name_template().format(
                    node_name=f"{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else BootstrapCore.AGGREGATED_LEVEL_NAME
                ):
                # value
                {
                    "description": f"Dataset for '{BootstrapCore.AGGREGATED_LEVEL_NAME}' Owner groups",
                    # "metadata": "",
                    "external_id": f"{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else BootstrapCore.AGGREGATED_LEVEL_NAME,
                }
                # creating 'all' at group type level + top-level
                for ns_name in list([ns.ns_name for ns in self.bootstrap_config.namespaces]) + [""]
            }
        )

        return target_datasets

    def generate_missing_datasets(self) -> Tuple[List[str], List[str]]:
        target_datasets = self.generate_target_datasets()

        # which targets are not already deployed?
        missing_datasets = {
            name: payload for name, payload in target_datasets.items() if name not in self.deployed.datasets.get_names()
        }

        if missing_datasets:
            # create all datasets which are not already deployed
            # https://docs.cognite.com/api/v1/#operation/createDataSets
            datasets_to_be_created = [
                DataSet(
                    name=name,
                    description=payload.get("description"),
                    external_id=payload.get("external_id"),
                    metadata=payload.get("metadata"),
                    write_protected=True,
                )
                for name, payload in missing_datasets.items()
            ]
            if self.is_dry_run:
                _logger.info(f"Dry run - Creating missing datasets: {[name for name in missing_datasets]}")
                _logger.debug(f"Dry run - Creating missing datasets (details): <{datasets_to_be_created}>")
            else:
                created_datasets: Union[DataSet, DataSetList] = self.client.data_sets.create(datasets_to_be_created)
                self.deployed.datasets.create(resources=created_datasets)

        # which targets are already deployed?
        # TODO: refactoring?
        existing_datasets = {
            # dictionary generator
            # key:
            ds.name:
            # value
            # Merge dataset 'id' from CDF with dataset arguments from config.yml
            dict(id=ds.id, **target_datasets[ds.name])
            for ds in self.deployed.datasets
            if ds.name in target_datasets.keys()
        }

        if existing_datasets:
            # update datasets which are already deployed
            # https://docs.cognite.com/api/v1/#operation/createDataSets
            # TODO: description, metadata, externalId
            datasets_to_be_updated = [
                DataSetUpdate(id=dataset["id"])
                .name.set(name)
                .description.set(dataset.get("description"))
                .external_id.set(dataset.get("external_id"))
                .metadata.set(dataset.get("metadata"))
                for name, dataset in existing_datasets.items()
            ]
            if self.is_dry_run:
                # cannot get easy the ds.name out of a DataSetUpdate object > using existing_datasets for logging
                _logger.info(f"Dry run - Updating existing datasets: {[name for name in existing_datasets]}")
                # dump of DataSetUpdate object
                _logger.debug(f"Dry run - Updating existing datasets (details): <{datasets_to_be_updated}>")
            else:
                updated_datasets: Union[DataSet, DataSetList] = self.client.data_sets.update(datasets_to_be_updated)
                self.deployed.datasets.update(resources=updated_datasets)

        return list(target_datasets.keys()), list(missing_datasets.keys())

    def generate_target_raw_dbs(self) -> Set[str]:
        # list of all targets: autogenerated raw_db names
        target_raw_db_names = set(
            [
                self.get_raw_dbs_name_template().format(node_name=ns_node.node_name, raw_variant=raw_variant)
                for ns in self.bootstrap_config.namespaces
                for ns_node in ns.ns_nodes
                for raw_variant in BootstrapCore.RAW_VARIANTS
            ]
        )
        target_raw_db_names.update(
            # add RAW DBs for 'all' users
            [
                self.get_raw_dbs_name_template().format(
                    node_name=f"{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else BootstrapCore.AGGREGATED_LEVEL_NAME,
                    raw_variant=raw_variant,
                )
                # creating allprojects at group type level + top-level
                for ns_name in list([ns.ns_name for ns in self.bootstrap_config.namespaces]) + [""]
                for raw_variant in BootstrapCore.RAW_VARIANTS
            ]
        )

        return target_raw_db_names

    def generate_missing_raw_dbs(self) -> Tuple[List[str], List[str]]:
        target_raw_db_names = self.generate_target_raw_dbs()

        try:
            # which targets are not already deployed?
            missing_rawdb_names = target_raw_db_names - set(self.deployed.raw_dbs.get_names())
        except Exception as exc:
            _logger.info(f"RAW databases do not exist in CDF:\n{exc}")
            missing_rawdb_names = target_raw_db_names

        if missing_rawdb_names:
            # create all raw_dbs which are not already deployed
            if self.is_dry_run:
                for raw_db in list(missing_rawdb_names):
                    _logger.info(f"Dry run - Creating rawdb: <{raw_db}>")
            else:
                created_rawdbs: Union[Database, DatabaseList] = self.client.raw.databases.create(
                    list(missing_rawdb_names)
                )
                self.deployed.raw_dbs.create(resources=created_rawdbs)

        return target_raw_db_names, missing_rawdb_names

    """
    "Special CDF groups" are groups which don't have capabilities but have an effect by their name only.
    1. 'transformations' group: grants access to "Fusion > Integrate > Transformations"
    2. 'extractors' group: grants access to "Fusion > Integrate > Extract Data" which allows dowload of extractors

    Both of them are about getting deprecated in the near future (time of writing: Q4 '21).
    - 'transformations' can already be replaced with dedicated 'transformationsAcl' capabilities
    - 'extractors' only used to grant access to extractor-download page
    """

    def generate_special_groups(self):

        special_group_names = ["extractors", "transformations"]
        _logger.info(f"Generating special groups:\n{special_group_names}")

        for special_group_name in special_group_names:
            self.create_group(group_name=special_group_name)

    # generate all groups - iterating through the 3-level hierarchy
    def generate_groups(self):
        # permutate the combinations
        for action in ["read", "owner"]:  # action_dimensions w/o 'admin'
            for ns in self.bootstrap_config.namespaces:
                for ns_node in ns.ns_nodes:
                    # group for each dedicated group-type id
                    self.process_group(action, ns.ns_name, ns_node.node_name)
                # 'all' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                self.process_group(action, ns.ns_name)
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            self.process_group(action)
        # creating CDF group for root_account (highest admin-level)
        for root_account in ["root"]:
            self.process_group(root_account=root_account)

    # prepare a yaml for "delete" job
    def dump_delete_template_to_yaml(self) -> None:
        # and reload again now with latest group config too

        # log cdf resource counts
        self.deployed.log_counts()

        delete_template = yaml.dump(
            {
                "delete_or_deprecate": {
                    "raw_dbs": [],
                    "datasets": [],
                    "groups": [],
                },
                "latest_deployment": {
                    "raw_dbs": sorted(self.deployed.raw_dbs.get_names()),
                    # (.. or "") because dataset names can be empty (None value)
                    "datasets": sorted(self.deployed.datasets.get_names()),
                    # (.. or "") because group names can be empty (None value)
                    "groups": sorted(self.deployed.groups.get_names()),
                },
            }
        )
        _logger.info(f"Delete template:\n{delete_template}")
        # return delete_template

    """
    ### create / delete
    * new in config
    * delete removed from config
    """

    def dry_run(self, dry_run: YesNoType) -> T_BootstrapCore:
        self.is_dry_run = dry_run == YesNoType.yes

        if self.is_dry_run:
            _logger.info("DRY-RUN active: No changes will be made to CDF")

        # return self for command chaining
        return self

    # '''
    #  oo.ooooo.  oooo d8b  .ooooo.  oo.ooooo.   .oooo.   oooo d8b  .ooooo.
    #   888' `88b `888""8P d88' `88b  888' `88b `P  )88b  `888""8P d88' `88b
    #   888   888  888     888ooo888  888   888  .oP"888   888     888ooo888
    #   888   888  888     888    .o  888   888 d8(  888   888     888    .o
    #   888bod8P' d888b    `Y8bod8P'  888bod8P' `Y888""8o d888b    `Y8bod8P'
    #   888                           888
    #  o888o                         o888o
    # '''
    def prepare(self, idp_source_id: str) -> None:
        group_name = "cdf:bootstrap"
        # group_name = f"{create_config.environment}:bootstrap"

        group_capabilities = [
            {"datasetsAcl": {"actions": ["READ", "WRITE", "OWNER"], "scope": {"all": {}}}},
            {"rawAcl": {"actions": ["READ", "WRITE", "LIST"], "scope": {"all": {}}}},
            {"groupsAcl": {"actions": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"], "scope": {"all": {}}}},
            {"projectsAcl": {"actions": ["READ", "UPDATE"], "scope": {"all": {}}}},
        ]

        # TODO: replace with dataclass
        idp_mapping = [
            # sourceId
            idp_source_id,
            # sourceName
            f"IdP group ID: {idp_source_id}",
        ]

        _logger.debug(f"GROUPS in CDF:\n{self.deployed.groups}")

        # allows idempotent creates, as it cleans up old groups with same names after creation
        self.create_group(group_name=group_name, group_capabilities=group_capabilities, idp_mapping=idp_mapping)
        if not self.is_dry_run:
            _logger.info(f"Created CDF group {group_name}")
        _logger.info("Finished CDF Project Bootstrapper in 'prepare' mode ")

    # '''
    #        .o8            oooo                .
    #       "888            `888              .o8
    #   .oooo888   .ooooo.   888   .ooooo.  .o888oo  .ooooo.
    #  d88' `888  d88' `88b  888  d88' `88b   888   d88' `88b
    #  888   888  888ooo888  888  888ooo888   888   888ooo888
    #  888   888  888    .o  888  888    .o   888 . 888    .o
    #  `Y8bod88P" `Y8bod8P' o888o `Y8bod8P'   "888" `Y8bod8P'
    # '''
    def delete(self):

        # groups
        group_names = self.delete_or_deprecate["groups"]
        if group_names:
            delete_group_ids = [g.id for g in self.deployed.groups if g.name in group_names]
            if delete_group_ids:
                # only delete groups which exist
                _logger.info(f"DELETE groups: {group_names}")
                if self.is_dry_run:
                    _logger.info(f"Dry run - Deprecating groups: <{group_names}>")
                else:
                    self.client.iam.groups.delete(delete_group_ids)
                    self.deployed.groups.delete(resources=self.deployed.groups.select(values=delete_group_ids))

            else:
                _logger.info(f"Groups already deleted: {group_names}")
        else:
            _logger.info("No groups to delete")

        # raw_dbs
        raw_db_names = self.delete_or_deprecate["raw_dbs"]
        if raw_db_names:
            delete_raw_db_names = list(set(raw_db_names).intersection(set(self.deployed.raw_dbs.get_names())))
            if delete_raw_db_names:
                # only delete dbs which exist
                # print("DELETE raw_dbs recursive with tables: ", raw_db_names)
                _logger.info(f"DELETE raw_dbs recursive with tables: {raw_db_names}")
                if self.is_dry_run:
                    _logger.info(f"Dry run - Deprecating raw_dbs: <{raw_db_names}>")
                else:
                    self.client.raw.databases.delete(delete_raw_db_names, recursive=True)
                    self.deployed.raw_dbs.delete(resources=self.deployed.raw_dbs.select(values=delete_raw_db_names))
            else:
                # print(f"RAW DBs already deleted: {raw_db_names}")
                _logger.info(f"RAW DBs already deleted: {raw_db_names}")
        else:
            _logger.info("No RAW Databases to delete")

        # datasets cannot be deleted by design
        # deprecate/archive them by prefix name with "_DEPR_", setting
        # "archive=true" and a "description" with timestamp of deprecation
        dataset_names = self.delete_or_deprecate["datasets"]
        if dataset_names:
            # get datasets which exists by name
            delete_datasets = [ds for ds in self.deployed.datasets if ds.name in dataset_names]
            if delete_datasets:
                for ds in delete_datasets:
                    _logger.info(f"DEPRECATE dataset: {ds.name}")
                    update_dataset = self.client.data_sets.retrieve(id=ds.id)
                    update_dataset.name = (
                        f"_DEPR_{update_dataset.name}"
                        if not update_dataset.name.startswith("_DEPR_")
                        else f"{update_dataset.name}"
                    )  # don't stack the DEPR prefixes
                    update_dataset.description = "Deprecated {}".format(self.get_timestamp())
                    update_dataset.metadata = dict(update_dataset.metadata, archived=True)  # or dict(a, **b)
                    update_dataset.external_id = f"_DEPR_{update_dataset.external_id}_[{self.get_timestamp()}]"
                    if self.is_dry_run:
                        _logger.info(f"Dry run - Deprecated dataset details: <{update_dataset}>")
                    else:
                        updated_datasets = self.client.data_sets.update(update_dataset)
                        self.deployed.datasets.update(resources=updated_datasets)

        else:
            _logger.info("No datasets to archive (and mark as deprecated)")

        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        _logger.info("Finished deleting CDF groups, datasets and RAW Databases")
        self.dump_delete_template_to_yaml()
        # TODO: write to file or standard output
        _logger.info("Finished deleting CDF groups, datasets and RAW Databases")

    # '''
    #        .o8                       oooo
    #       "888                       `888
    #   .oooo888   .ooooo.  oo.ooooo.   888   .ooooo.  oooo    ooo
    #  d88' `888  d88' `88b  888' `88b  888  d88' `88b  `88.  .8'
    #  888   888  888ooo888  888   888  888  888   888   `88..8'
    #  888   888  888    .o  888   888  888  888   888    `888'
    #  `Y8bod88P" `Y8bod8P'  888bod8P' o888o `Y8bod8P'     .8'
    #                        888                       .o..P'
    #                       o888o                      `Y8P'
    # '''
    def deploy(self, with_special_groups: YesNoType, with_raw_capability: YesNoType) -> None:

        # store parameter as bool
        # if provided they override configuration or defaults from yaml-config
        if with_special_groups:
            self.with_special_groups = with_special_groups == YesNoType.yes
        if with_raw_capability:
            self.with_raw_capability = with_raw_capability == YesNoType.yes

        # debug new features and override with cli-parameters
        _logger.info(f"From cli: {with_special_groups=} / {with_raw_capability=}")
        _logger.info(f"Effective: {self.with_special_groups=} / {self.with_raw_capability=}")

        # load deployed groups, datasets, raw_dbs with their ids and metadata
        _logger.info(f"RAW_DBS in CDF:\n{self.deployed.raw_dbs.get_names()}")
        _logger.info(f"DATASETS in CDF:\n{self.deployed.datasets.get_names()}")
        _logger.info(f"GROUPS in CDF:\n{self.deployed.groups.get_names()}")

        # run generate steps (only print results atm)

        target_raw_db_names: List[str] = []
        new_created_raw_db_names: List[str] = []
        if self.with_raw_capability:
            target_raw_db_names, new_created_raw_db_names = self.generate_missing_raw_dbs()
            _logger.info(f"All RAW_DBS from config:\n{target_raw_db_names}")
            _logger.info(f"New RAW_DBS to CDF:\n{new_created_raw_db_names}")
        else:
            # no RAW DBs means no access to RAW at all
            # which means no 'rawAcl' capability to create
            # remove it form the default types
            _logger.info("Creating no RAW_DBS and no 'rawAcl' capability")
            acl_default_types.remove("raw")

        target_dataset_names, new_created_dataset_names = self.generate_missing_datasets()
        _logger.info(f"All DATASETS from config:\n{target_dataset_names}")
        _logger.info(f"New DATASETS to CDF:\n{new_created_dataset_names}")

        # store all raw_dbs and datasets in scope of this configuration
        self.all_scope_ctx = {
            "raw": target_raw_db_names,  # all raw_dbs
            "datasets": target_dataset_names,  # all datasets
        }

        # TODO: update CogniteDeployedCache with datasets/ids!

        # Special CDF groups and their aad_mappings
        if with_special_groups == YesNoType.yes:
            self.generate_special_groups()

        # CDF groups from configuration
        self.generate_groups()
        if not self.is_dry_run:
            _logger.info("Created new CDF groups")

        # and reload again now with latest group config too
        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        _logger.info("Finished creating CDF groups, datasets and RAW Databases")
        self.dump_delete_template_to_yaml()

        _logger.info(f"Final RAW_DBS in CDF:\n{self.deployed.raw_dbs.get_names()}")
        _logger.info(f"Final DATASETS in CDF:\n{self.deployed.datasets.get_names()}")
        _logger.info(f"Final GROUPS in CDF\n{self.deployed.groups.get_names()}")

        # _logger.info(f'Bootstrap Pipelines: created: {len(created)}, deleted: {len(delete_ids)}')

    # '''
    #        .o8   o8o
    #       "888   `"'
    #   .oooo888  oooo   .oooo.    .oooooooo oooo d8b  .oooo.   ooo. .oo.  .oo.
    #  d88' `888  `888  `P  )88b  888' `88b  `888""8P `P  )88b  `888P"Y88bP"Y88b
    #  888   888   888   .oP"888  888   888   888      .oP"888   888   888   888
    #  888   888   888  d8(  888  `88bod8P'   888     d8(  888   888   888   888
    #  `Y8bod88P" o888o `Y888""8o `8oooooo.  d888b    `Y888""8o o888o o888o o888o
    #                             d"     YD
    #                             "Y88888P'
    # '''

    def diagram(
        self,
        to_markdown: YesNoType = YesNoType.no,
        with_raw_capability: YesNoType = YesNoType.yes,
        cdf_project: str = None,
    ) -> None:
        """Diagram mode used to document the given configuration as a Mermaid diagram.

        Args:
            to_markdown (YesNoType, optional):
              - Encapsulate Mermaid diagram in Markdown syntax.
              - Defaults to 'YesNoType.no'.
            with_raw_capability (YesNoType, optional):
              - Create RAW DBs and 'rawAcl' capability. Defaults to 'YesNoType.tes'.
            cdf_project (str, optional):
              - Provide the CDF Project to use for the diagram 'idp-cdf-mappings'.

        Example:
            # requires a 'cognite' configuration section
            ➟  poetry run bootstrap-cli diagram configs/config-deploy-example-v2.yml | clip.exe
            # precedence over 'cognite.project' which CDF Project to diagram 'bootstrap.idp-cdf-mappings'
            # making a 'cognite' section optional
            ➟  poetry run bootstrap-cli diagram --cdf-project shiny-dev configs/config-deploy-example-v2.yml | clip.exe
            # precedence over configuration 'bootstrap.features.with-raw-capability'
            ➟  poetry run bootstrap-cli diagram --with-raw-capability no --cdf-project shiny-prod configs/config-deploy-example-v2.yml
        """  # noqa

        diagram_cdf_project = cdf_project if cdf_project else self.cdf_project
        # same handling as in 'deploy' command
        # store parameter as bool
        # if available it overrides configuration or defaults from yaml-config
        if with_raw_capability:
            self.with_raw_capability = with_raw_capability == YesNoType.yes

        # debug new features and override with cli-parameters
        _logger.info(f"From cli: {with_raw_capability=}")
        _logger.info(f"Effective: {self.with_raw_capability=}")

        # store all raw_dbs and datasets in scope of this configuration
        self.all_scope_ctx = {
            "owner": (
                all_scopes := {
                    # generate_target_raw_dbs -> returns a Set[str]
                    "raw": list(self.generate_target_raw_dbs()),  # all raw_dbs
                    # generate_target_datasets -> returns a Dict[str, Any]
                    "datasets": list(self.generate_target_datasets().keys()),  # all datasets
                }
            ),
            # and copy the same to 'read'
            "read": all_scopes,
        }

        def get_group_name_and_scopes(
            action: str = None, ns_name: str = None, node_name: str = None, root_account: str = None
        ) -> Tuple[str, Dict[str, Any]]:
            """Adopted generate_group_name_and_capabilities() and get_scope_ctx_groupedby_action()
            to respond with
            - the full-qualified CDF group name and
            - all scopes sorted by action [read|owner] and [raw|datasets]

            TODO: support 'root'

            Args:
                action (str, optional):
                    One of the action_dimensions ["read", "owner"].
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

                Returns:
                    Tuple[str, Dict[str, Any]]: (group_name, scope_ctx_by_action)
                        scope_ctx_by_action is a dictionary with the following structure:
                            {'owner': {
                                'raw': ['src:002:weather:rawdb', 'src:002:weather:rawdb:state'],
                                'datasets': ['src:002:weather:dataset']
                                },
                            'read': {
                                'raw': [],
                                'datasets': []
                            }}
            """

            group_name_full_qualified, scope_ctx_by_action = None, None

            # detail level like cdf:src:001:public:read
            if action and ns_name and node_name:
                group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{node_name}:{action}"
                scope_ctx_by_action = self.get_scope_ctx_groupedby_action(action, ns_name, node_name)

            # group-type level like cdf:src:all:read
            elif action and ns_name:
                # 'all' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                group_name_full_qualified = (
                    f"{BootstrapCore.GROUP_NAME_PREFIX}{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}"
                )
                scope_ctx_by_action = self.get_scope_ctx_groupedby_action(action, ns_name)

            # top level like cdf:all:read
            elif action:
                # 'all' groups on action level (no limits to datasets or raw-dbs)
                group_name_full_qualified = (
                    f"{BootstrapCore.GROUP_NAME_PREFIX}{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}"
                )
                # limit all_scopes to 'action'
                scope_ctx_by_action = {action: self.all_scope_ctx[action]}
            # root level like cdf:root
            elif root_account:  # no parameters
                # all (no limits)
                group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{root_account}"

            return group_name_full_qualified, scope_ctx_by_action

        class SubgraphTypes(str, Enum):
            idp = "IdP Groups"
            owner = "'Owner' Groups"
            read = "'Read' Groups"
            # OWNER
            core_cdf_owner = "Node Level (Owner)"
            ns_cdf_owner = "Namespace Level (Owner)"
            scope_owner = "Scopes (Owner)"
            # READ
            core_cdf_read = "Node Level (Read)"
            ns_cdf_read = "Namespace Level (Read)"
            scope_read = "Scopes (Read)"

        # TODO: refactoring required
        def group_to_graph(
            graph: GraphRegistry,
            action: str = None,
            ns_name: str = None,
            node_name: str = None,
            root_account: str = None,
        ) -> None:

            if root_account:
                return

            group_name, scope_ctx_by_action = get_group_name_and_scopes(action, ns_name, node_name, root_account)

            # check lookup from provided config
            mapping = self.bootstrap_config.get_idp_cdf_mapping_for_group(
                # diagram explicit given cdf_project, or configured in 'cognite' configuration section
                cdf_project=diagram_cdf_project,
                cdf_group=group_name,
            )
            # unpack
            # idp_source_id, idp_source_name = self.aad_mapping_lookup.get(node_name, [None, None])
            idp_source_id, idp_source_name = mapping.idp_source_id, mapping.idp_source_name

            _logger.info(f"{ns_name=} : {group_name=} : {scope_ctx_by_action=} [{idp_source_name=}]")

            # preload master subgraphs
            core_cdf = graph.get_or_create(getattr(SubgraphTypes, f"core_cdf_{action}"))
            ns_cdf_graph = graph.get_or_create(getattr(SubgraphTypes, f"ns_cdf_{action}"))
            scope_graph = graph.get_or_create(getattr(SubgraphTypes, f"scope_{action}"))

            #
            # NODE - IDP GROUP
            #
            idp = graph.get_or_create(SubgraphTypes.idp)
            if idp_source_name and (idp_source_name not in idp):
                idp.elements.append(
                    TrapezNode(
                        id_name=idp_source_name,
                        display=idp_source_name,
                        comments=[f'IdP objectId: {idp_source_id}']
                        )
                    )  # fmt: skip
                graph.edges.append(
                    Edge(
                        id_name=idp_source_name,
                        dest=group_name,
                        annotation=None,
                        comments=[]
                        )
                    )  # fmt: skip

            # {'owner': {'raw': ['src:002:weather:rawdb', 'src:002:weather:rawdb:state'],
            #       'datasets': ['src:002:weather:dataset']},
            # 'read': {'raw': [], 'datasets': []}}

            #
            # NODE - CORE LEVEL
            #   'cdf:src:001:public:read'
            #
            if action and ns_name and node_name:
                core_cdf.elements.append(
                    RoundedNode(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                        )
                    )  # fmt: skip

                #
                # EDGE FROM PARENT 'src:all' to 'src:001:sap'
                #
                edge_type_cls = Edge if action == "owner" else DottedEdge
                graph.edges.append(
                    edge_type_cls(
                        # link from all:{ns}
                        # multiline f-string split as it got too long
                        # TODO: refactor into string-templates
                        id_name=f"{BootstrapCore.GROUP_NAME_PREFIX}{ns_name}:"
                        f"{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}",
                        dest=group_name,
                        annotation="",
                        comments=[],
                    )
                )  # fmt: skip

                # add core and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type == "raw":
                            continue  # SKIP RAW

                        for scope_name in scopes:

                            #
                            # NODE DATASET or RAW scope
                            #    'src:001:sap:rawdb'
                            #
                            if scope_name not in scope_graph:
                                node_type_cls = SubroutineNode if scope_type == "raw" else AssymetricNode
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                        )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:src:001:sap:read to 'src:001:sap:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == "owner" else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

            #
            # NODE - NAMESPACE LEVEL
            #   'src:all:read' or 'src:all:owner'
            elif action and ns_name:
                ns_cdf_graph.elements.append(
                    Node(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                        )
                    )  # fmt: skip

                #
                # EDGE FROM PARENT top LEVEL to NAMESPACE LEVEL
                #   'all' to 'src:all'
                #
                edge_type_cls = Edge if action == "owner" else DottedEdge
                graph.edges.append(
                    edge_type_cls(
                        id_name=f"{BootstrapCore.GROUP_NAME_PREFIX}{BootstrapCore.AGGREGATED_LEVEL_NAME}:{action}",
                        dest=group_name,
                        annotation="",
                        comments=[],
                    )
                )  # fmt: skip

                # add namespace-node and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type == "raw":
                            continue  # SKIP RAW

                        for scope_name in scopes:

                            # LIMIT only to direct scopes for readability
                            # which have for example 'src:all:' as prefix
                            if not scope_name.startswith(f"{ns_name}:{BootstrapCore.AGGREGATED_LEVEL_NAME}:"):
                                continue

                            #
                            # NODE DATASET or RAW scope
                            #    'src:all:rawdb'
                            #
                            if scope_name not in scope_graph:

                                node_type_cls = SubroutineNode if scope_type == "raw" else AssymetricNode
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                        )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:src:all:read to 'src:all:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == "owner" else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

            #
            # NODE - TOP LEVEL
            #   like `cdf:all:read`
            #
            elif action:
                ns_cdf_graph.elements.append(
                    Node(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                        )
                    )  # fmt: skip

                # add namespace-node and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type == "raw":
                            continue  # SKIP RAW

                        for scope_name in scopes:

                            # LIMIT only to direct scopes for readability
                            # which have for example 'src:all:' as prefix
                            if not scope_name.startswith(f"{BootstrapCore.AGGREGATED_LEVEL_NAME}:"):
                                continue

                            # _logger.info(f"> {action=} {shared_action=} process {scope_name=} : all {scopes=}")
                            #
                            # NODE DATASET or RAW scope
                            #    'all:rawdb'
                            #
                            if scope_name not in scope_graph:

                                # _logger.info(f">> add {scope_name=}__{action=}")

                                node_type_cls = SubroutineNode if scope_type == "raw" else AssymetricNode
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                        )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:all:read to 'all:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == "owner" else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

        #
        # finished inline helper-methods
        # starting diagram logic
        #

        if not self.with_raw_capability:
            # no RAW DBs means no access to RAW at all
            # which means no 'rawAcl' capability to create
            # remove it form the default types
            _logger.info("Without RAW_DBS and 'rawAcl' capability")
            acl_default_types.remove("raw")

        # sorting relationship output into potential subgraphs
        graph = GraphRegistry()
        # top subgraphs (three columns layout)
        # provide Subgraphs with a 'subgraph_name' and a 'subgraph_short_name'
        # using the SubgraphTypes enum 'name' (default) and 'value' properties
        idp_group = graph.get_or_create(
            SubgraphTypes.idp, f"{SubgraphTypes.idp.value} for CDF: '{diagram_cdf_project}'"
        )
        owner = graph.get_or_create(SubgraphTypes.owner, SubgraphTypes.owner.value)
        read = graph.get_or_create(SubgraphTypes.read, SubgraphTypes.read.value)

        # nested subgraphs
        core_cdf_owner = graph.get_or_create(SubgraphTypes.core_cdf_owner, SubgraphTypes.core_cdf_owner.value)
        ns_cdf_owner = graph.get_or_create(SubgraphTypes.ns_cdf_owner, SubgraphTypes.ns_cdf_owner.value)
        core_cdf_read = graph.get_or_create(SubgraphTypes.core_cdf_read, SubgraphTypes.core_cdf_read.value)
        ns_cdf_read = graph.get_or_create(SubgraphTypes.ns_cdf_read, SubgraphTypes.ns_cdf_read.value)
        scope_owner = graph.get_or_create(SubgraphTypes.scope_owner, SubgraphTypes.scope_owner.value)
        scope_read = graph.get_or_create(SubgraphTypes.scope_read, SubgraphTypes.scope_read.value)

        # add the three top level groups to our graph
        graph.elements.extend(
            [
                idp_group,
                owner,
                read,
                # doc_group
            ]
        )
        # add/nest the owner-subgraphs to its parent subgraph
        owner.elements.extend(
            [
                core_cdf_owner,
                ns_cdf_owner,
                scope_owner,
            ]
        )
        # add/nest the read-subgraphs to its parent subgraph
        read.elements.extend(
            [
                core_cdf_read,
                ns_cdf_read,
                scope_read,
            ]
        )

        # permutate the combinations
        for action in ["read", "owner"]:  # action_dimensions w/o 'admin'
            for ns in self.bootstrap_config.namespaces:
                for ns_node in ns.ns_nodes:
                    # group for each dedicated group-type id
                    group_to_graph(graph, action, ns.ns_name, ns_node.node_name)
                # 'all' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                group_to_graph(graph, action, ns.ns_name)
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            group_to_graph(graph, action)
        # all (no limits + admin)
        # 211013 pa: for AAD root:client and root:user can be merged into 'root'
        # for root_account in ["root:client", "root:user"]:
        for root_account in ["root"]:
            group_to_graph(graph, root_account=root_account)

        mermaid_code = graph.to_mermaid()

        _logger.info(f"Generated {len(mermaid_code)} characters")

        markdown_wrapper_template = """
## auto-generated by bootstrap-cli
```mermaid
{mermaid_code}
```"""
        # print to stdout that only the diagram can be piped to clipboard or file
        print(
            markdown_wrapper_template.format(mermaid_code=mermaid_code)
            if to_markdown == YesNoType.yes
            else mermaid_code
        )


# '''
#           888 d8b          888
#           888 Y8P          888
#           888              888
#   .d8888b 888 888  .d8888b 888  888
#  d88P"    888 888 d88P"    888 .88P
#  888      888 888 888      888888K
#  Y88b.    888 888 Y88b.    888 "88b
#   "Y8888P 888 888  "Y8888P 888  888
# '''


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(prog_name="bootstrap_cli", version=__version__)
@click.option(
    "--cdf-project-name",
    help="CDF Project to interact with the CDF API, the 'BOOTSTRAP_CDF_PROJECT',"
    "environment variable can be used instead. Required for OAuth2 and optional for api-keys.",
    envvar="BOOTSTRAP_CDF_PROJECT",
)
# TODO: is cluster and alternative for host?
@click.option(
    "--cluster",
    default="westeurope-1",
    help="The CDF cluster where CDF Project is hosted (e.g. greenfield, europe-west1-1),"
    "Provide this or make sure to set the 'BOOTSTRAP_CDF_CLUSTER' environment variable. "
    "Default: westeurope-1",
    envvar="BOOTSTRAP_CDF_CLUSTER",
)
@click.option(
    "--host",
    default="https://bluefield.cognitedata.com/",
    help="The CDF host where CDF Project is hosted (e.g. https://bluefield.cognitedata.com),"
    "Provide this or make sure to set the 'BOOTSTRAP_CDF_HOST' environment variable."
    "Default: https://bluefield.cognitedata.com/",
    envvar="BOOTSTRAP_CDF_HOST",
)
@click.option(
    "--api-key",
    help="API key to interact with the CDF API. Provide this or make sure to set the 'BOOTSTRAP_CDF_API_KEY',"
    "environment variable if you want to authenticate with API keys.",
    envvar="BOOTSTRAP_CDF_API_KEY",
)
@click.option(
    "--client-id",
    help="IdP client ID to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_CLIENT_ID' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_ID",
)
@click.option(
    "--client-secret",
    help="IdP client secret to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_CLIENT_SECRET' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_SECRET",
)
@click.option(
    "--token-url",
    help="IdP token URL to interact with the CDF API. Provide this or make sure to set the "
    "'BOOTSTRAP_IDP_TOKEN_URL' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_TOKEN_URL",
)
@click.option(
    "--scopes",
    help="IdP scopes to interact with the CDF API, relevant for OAuth2 authentication method. "
    "The 'BOOTSTRAP_IDP_SCOPES' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_SCOPES",
)
@click.option(
    "--audience",
    help="IdP Audience to interact with the CDF API, relevant for OAuth2 authentication method. "
    "The 'BOOTSTRAP_IDP_AUDIENCE' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_AUDIENCE",
)
@click.option(
    "--dotenv-path",
    help="Provide a relative or absolute path to an .env file (for command line usage only)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print debug information",
)
@click.option(
    "--dry-run",
    default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Log only planned CDF API actions while doing nothing." " Defaults to 'no'.",
)
@click.pass_context
def bootstrap_cli(
    # click.core.Context
    context: Context,
    # cdf
    cluster: str = "westeurope-1",
    cdf_project_name: Optional[str] = None,
    host: str = None,
    api_key: Optional[str] = None,
    # cdf idp
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    scopes: Optional[str] = None,
    token_url: Optional[str] = None,
    audience: Optional[str] = None,
    # cli
    # TODO: dotenv_path: Optional[click.Path] = None,
    dotenv_path: Optional[str] = None,
    debug: bool = False,
    dry_run: str = "no",
) -> None:

    # load .env from file if exists, use given dotenv_path if provided
    load_dotenv(dotenv_path=dotenv_path)

    context.obj = {
        # cdf
        "cluster": cluster,
        "cdf_project_name": cdf_project_name,
        "host": host,
        "api_key": api_key,
        # cdf idp
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes,
        "token_url": token_url,
        "audience": audience,
        # cli
        "dotenv_path": dotenv_path,
        "debug": debug,
        "dry_run": dry_run,
    }


@click.command(help="Deploy a bootstrap configuration from a configuration file.")
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--with-special-groups",
    # having this as a flag is not working for gh-action 'actions.yml' manifest
    # instead using explicit choice options
    # is_flag=True,
    # default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create special CDF groups, without any capabilities (extractions, transformations). Defaults to 'no'",
)
@click.option(
    "--with-raw-capability",
    # default="yes", # default defined in 'configuration.BootstrapFeatures'
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create RAW databases and 'rawAcl' capability. Defaults to 'yes'",
)
@click.pass_obj
def deploy(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    with_special_groups: YesNoType,
    with_raw_capability: YesNoType,
) -> None:

    click.echo(click.style("Deploying CDF Project bootstrap...", fg="red"))

    if obj["debug"]:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        (
            BootstrapCore(config_file, command=CommandMode.DEPLOY)
            .validate_config_length_limits()
            .validate_config_is_cdf_project_in_mappings()
            .dry_run(obj["dry_run"])
            .deploy(
                with_special_groups=with_special_groups,
                with_raw_capability=with_raw_capability,
                )
        )  # fmt:skip

        click.echo(click.style("CDF Project bootstrap deployed", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Prepares an elevated CDF group 'cdf:bootstrap', using the same AAD group link "
    "as used for the initial 'oidc-admin-group' and "
    "with additional capabilities to run the 'deploy' and 'delete' commands next. "
    "You only need to run the 'prepare' command once per CDF project."
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
# TODO: support '--idp-source-id' as an option too, to match v2 naming changes?
@click.option(
    "--aad-source-id",
    "--idp-source-id",
    "idp_source_id",  # explicit named variable for alternatives
    required=True,
    help="Provide the IdP source ID to use for the 'cdf:bootstrap' group. "
    "Typically for a new project it's the same as configured for the initial "
    "CDF group named 'oidc-admin-group'. "
    "The parameter option '--aad-source-id' will be deprecated in next major release",
)
@click.pass_obj
def prepare(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    idp_source_id: str,
    dry_run: YesNoType = YesNoType.no,
) -> None:

    click.echo(click.style("Prepare CDF Project ...", fg="red"))

    if obj["debug"]:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        (
            BootstrapCore(config_file, command=CommandMode.PREPARE)
            # .validate_config() # TODO
            .dry_run(obj["dry_run"])
            .prepare(idp_source_id=idp_source_id)
        )  # fmt:skip

        click.echo(click.style("CDF Project bootstrap prepared for running 'deploy' command next.", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Delete mode used to delete CDF groups, datasets and RAW databases. "
    "CDF groups and RAW databases are deleted, while datasets are archived "
    "and deprecated (datasets cannot be deleted)."
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.pass_obj
def delete(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
) -> None:

    click.echo(click.style("Delete CDF Project ...", fg="red"))

    if obj["debug"]:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        (
            BootstrapCore(config_file, command=CommandMode.DELETE)
            # .validate_config() # TODO
            .dry_run(obj["dry_run"]).delete()
        )

        click.echo(
            click.style(
                "CDF Project relevant groups and raw_dbs are deleted and/or datasets are archived and deprecated ",
                fg="blue",
            )
        )

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(help="Diagram mode documents the given configuration as a Mermaid diagram")
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--markdown",
    default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Encapsulate the Mermaid diagram in Markdown syntax. " "Defaults to 'no'",
)
@click.option(
    "--with-raw-capability",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create RAW Databases and 'rawAcl' capability. " "Defaults to 'yes'",
)
@click.option(
    "--cdf-project",
    help="[optional] Provide the CDF project name to use for the diagram 'idp-cdf-mappings'.",
)
@click.pass_obj
def diagram(
    # click.core.Context obj
    obj: Dict,
    config_file: str,
    markdown: YesNoType,
    with_raw_capability: YesNoType,
    cdf_project: str,
) -> None:

    # click.echo(click.style("Diagram CDF Project ...", fg="red"))

    if obj["debug"]:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        (
            BootstrapCore(config_file, command=CommandMode.DIAGRAM)
            .validate_config_length_limits()
            .validate_config_is_cdf_project_in_mappings()
            # .dry_run(obj['dry_run'])
            .diagram(
                to_markdown=markdown,
                with_raw_capability=with_raw_capability,
                cdf_project=cdf_project,
                )
        )  # fmt:skip

        # click.echo(
        #     click.style(
        #         "CDF Project relevant groups and raw_dbs are documented as Mermaid",
        #         fg="blue",
        #     )
        # )

    except BootstrapConfigError as e:
        exit(e.message)


bootstrap_cli.add_command(deploy)
bootstrap_cli.add_command(prepare)
bootstrap_cli.add_command(delete)
bootstrap_cli.add_command(diagram)


def main() -> None:
    # call click.pass_context
    bootstrap_cli()


if __name__ == "__main__":
    main()
