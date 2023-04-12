import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple, TypeVar, Union

import yaml
from cognite.client import CogniteClient
from cognite.client.data_classes import Database, DatabaseList, DataSet, DataSetList, DataSetUpdate, Group, GroupList

# fdm sdk injection
# v2
# from fdm_sdk_inject.data_classes.data_model_storages.spaces import DataModelStorageSpace, DataModelStorageSpaceList
# v3
from fdm_sdk_inject.data_classes.models.spaces import ModelsSpace, ModelsSpaceList

from .. import __version__
from ..app_cache import CogniteDeployedCache
from ..app_config import (
    NEWLINE,
    AclAdminTypes,
    AclAllScopeOnlyTypes,
    AclDefaultTypes,
    ActionDimensions,
    BootstrapCoreConfig,
    BootstrapDeleteConfig,
    CommandMode,
    RoleType,
    ScopeCtxType,
    SharedAccess,
    YesNoType,
)
from ..app_container import ContainerSelector, init_container
from ..app_exceptions import BootstrapValidationError


class CommandBase:

    # CDF group prefix, i.e. "cdf:", to make bootstrap created CDF groups easy recognizable in Fusion
    GROUP_NAME_PREFIX = ""

    # mandatory for hierarchical-namespace
    AGGREGATED_LEVEL_NAME = ""

    # rawdbs creation support additional variants, for special purposes (like saving statestores)
    # - default-suffix is ':rawdb' with no variant-suffix (represented by "")
    # - additional variant-suffixes can be added like this ["", ":state"]
    RAW_VARIANTS = [""]

    def __init__(self, config_path: str, command: CommandMode, debug: bool, dry_run: bool = False):

        # validate and load config according to command-mode
        ContainerCls = ContainerSelector[command]
        self.container: ContainerCls = init_container(ContainerCls, config_path)

        # migrating to CogniteDeployedCache
        # self.deployed: Dict[str, Any] = {}
        self.deployed: CogniteDeployedCache = None
        self.all_scoped_ctx: Dict[str, Any] = {}
        self.is_dry_run: bool = dry_run
        self.client: CogniteClient = None
        self.cdf_project = None

        logging.info(f"Starting CDF Bootstrap version <v{__version__}> for command: <{command}>")
        if self.is_dry_run:
            logging.info("DRY-RUN activated: No changes will be made to CDF")

        # init command-specific parts
        # if subclass(ContainerCls, CogniteContainer):
        if command in (CommandMode.DEPLOY, CommandMode.DELETE, CommandMode.PREPARE):
            #
            # Cognite initialisation
            #
            self.client: CogniteClient = self.container.cognite_client()
            # TODO: support: token_custom_args
            # client_name="inso-bootstrap-cli", token_custom_args=self.config.token_custom_args

            self.cdf_project = self.client.config.project
            logging.info(f"Successful connection to CDF client to project: '{self.cdf_project}'")

            # load CDF group, dataset, rawdb config
            self.deployed = CogniteDeployedCache(self.client, groups_only=(command == CommandMode.PREPARE))
            self.deployed.log_counts()

        # not perfect refactoring yet, to handle the container/config parsing and loading for the different CommandModes
        match command:
            case CommandMode.DELETE:
                self.delete_or_deprecate: BootstrapDeleteConfig = self.container.delete_or_deprecate()

            case CommandMode.DEPLOY | CommandMode.DIAGRAM | CommandMode.PREPARE:

                # TODO: correct for DIAGRAM and PREPARE?!
                self.bootstrap_config: BootstrapCoreConfig = self.container.bootstrap()
                self.idp_cdf_mappings = self.bootstrap_config.idp_cdf_mappings

                if command == CommandMode.DIAGRAM:
                    # diagram, doesn't contain 'cognite' config
                    # but tries to read 'cognite.project' as default
                    # if no '--cdf-project' cli-parameter is given explicit.
                    # Accessing the 'container.config()' directly to check availability
                    # TODO: how to configure an optional 'cognite' section in container directly?
                    self.cdf_project = self.container.config().get("cognite", {}).get("project")

                #
                # load 'bootstrap.features'
                #
                # unpack and process features
                features = self.bootstrap_config.features

                # TODO: not available for 'delete' but there must be a smarter solution
                logging.debug(
                    "Features from config.yaml or defaults (can be overridden by cli-parameters!): " f"{features=}"
                )

                # [OPTIONAL] default: False
                self.with_special_groups: bool = features.with_special_groups
                # [OPTIONAL] default: True
                self.with_raw_capability: bool = features.with_raw_capability
                # [OPTIONAL] default: False
                self.with_datamodel_capability: bool = features.with_datamodel_capability

                # [OPTIONAL] default: "allprojects"
                CommandBase.AGGREGATED_LEVEL_NAME = features.aggregated_level_name
                # [OPTIONAL] default: "cdf:"
                # support for '' empty string
                CommandBase.GROUP_NAME_PREFIX = f"{features.group_prefix}:" if features.group_prefix else ""
                # [OPTIONAL] default: "dataset"
                # support for '' empty string
                CommandBase.DATASET_SUFFIX = f":{features.dataset_suffix}" if features.dataset_suffix else ""
                # [OPTIONAL] default: "space"
                # support for '' empty string
                CommandBase.SPACE_SUFFIX = f":{features.space_suffix}" if features.space_suffix else ""
                # [OPTIONAL] default: "rawdb"
                # support for '' empty string
                CommandBase.RAW_SUFFIX = f":{features.rawdb_suffix}" if features.rawdb_suffix else ""
                # [OPTIONAL] default: ["", ":state"]
                CommandBase.RAW_VARIANTS = [""] + [f":{suffix}" for suffix in features.rawdb_additional_variants]

    @staticmethod
    def acl_template(actions, scope):
        return {"actions": actions, "scope": scope}

    @staticmethod
    def get_allprojects_name_template(ns_name=None):
        return f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}" if ns_name else CommandBase.AGGREGATED_LEVEL_NAME

    @staticmethod
    def get_dataset_name_template():
        return "{node_name}" + CommandBase.DATASET_SUFFIX

    @staticmethod
    def get_space_name_template(node_name: str):
        # 'space' have to match this regex: ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,41}[a-zA-Z0-9]?$
        FDM_SPACE_RE = re.compile(r"[^a-zA-Z0-9-_]").sub
        # every charchter not matching this pattern will be replaced
        FDM_SPECIAL_CHAR_REPLACEMENT = "-"
        return FDM_SPACE_RE(FDM_SPECIAL_CHAR_REPLACEMENT, f"{node_name}{CommandBase.SPACE_SUFFIX}")

    @staticmethod
    def get_raw_dbs_name_template():
        return "{node_name}" + CommandBase.RAW_SUFFIX + "{raw_variant}"

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
        # TODO: space extid limit?
        SPACE_EXTERNALID_LENGTH_LIMIT = 44

        # create all required scopes to check name lengths
        all_scopes = {
            # generate_target_raw_dbs -> returns a Set[str]
            "raw": self.generate_target_raw_dbs(),  # all raw_dbs
            # generate_target_datasets -> returns a Dict[str, Any]
            "datasets": self.generate_target_datasets(),  # all datasets
            # # generate_target_spaces -> returns a Set[str]
            "spaces": self.generate_target_spaces(),  # all spaces
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
        if self.with_datamodel_capability:
            errors.extend(
                [
                    ("SPACE", space_name, len(space_name), RAWDB_NAME_LENGTH_LIMIT)
                    for space_name in all_scopes["spaces"]
                    if len(space_name) > SPACE_EXTERNALID_LENGTH_LIMIT
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

    def validate_config_shared_access(self):
        """Check shared-access configuration, that all node-names exist

        Returns:
            self: allows validation chaining
        """
        errors = []

        # collect all explicit node-names
        ns_node_names = [ns_node.node_name for ns in self.bootstrap_config.namespaces for ns_node in ns.ns_nodes]

        # add aggregated node-names (using AGGREGATED_LEVEL_NAME)
        ns_node_names.extend(
            [CommandBase.get_allprojects_name_template()]  # top-level
            + [
                CommandBase.get_allprojects_name_template(ns_name=ns.ns_name)  # ns-level
                for ns in self.bootstrap_config.namespaces
            ]
        )

        # check for each node-name if a shared-access exists
        for node_name in ns_node_names:
            if shared_access := self.get_ns_node_shared_access_by_name(node_name):
                errors.extend(
                    [
                        # collect node | role | invalid shared-access node-name
                        (node_name, role, shared_node.node_name)
                        for role in [RoleType.OWNER, RoleType.READ]
                        for shared_node in getattr(shared_access, role)
                        if shared_node.node_name not in ns_node_names
                    ]
                )

        if errors:
            raise BootstrapValidationError(
                "Shared Access validation error(s):\n"
                # RAW DB src:002:weather:rawdbiswaytoolongtofit : len(38) > 32
                f"""{NEWLINE.join(
                    [
                        f'{i+1}. Non existent node-name reference "{invalid_shared_access_node_name}" found'
                        f' in "{node_name}".shared-access.{role}'
                        for i, (node_name, role, invalid_shared_access_node_name) in enumerate(errors)
                    ])}"""
            )

        return self

    def validate_cdf_project_available(self, cdf_project_from_cli: str):
        # diagram, doesn't require 'cognite' config
        # using the container to check if one exists and read its 'project' name

        if not cdf_project_from_cli and not self.cdf_project:
            raise ValueError(
                "No --cdf-project or 'cognite' configuration is given. No idp-cdf-mapping possible in diagram"
            )

        # return self for chaining
        return self

    def validate_config_is_cdf_project_in_mappings(self, cdf_project_from_cli: str = None):

        # check if mapping exists for configured cdf-project
        # or for explicit configured cli parameter ('diagram' only)
        check_cdf_project = cdf_project_from_cli or self.cdf_project
        is_cdf_project_in_mappings = check_cdf_project in [mapping.cdf_project for mapping in self.idp_cdf_mappings]

        if not is_cdf_project_in_mappings:
            logging.warning(f"No 'idp-cdf-mapping' found for CDF Project <{check_cdf_project}>")
            # log or raise?
            # raise ValueError(f'No mapping for CDF project {self.cdf_project}')

        # return self for chainingself.core.
        return self

    def generate_default_action(self, action: RoleType, acl_type: str) -> List[str]:
        """bootstrap-cli supports two roles: READ, OWNER (called action as parameter)
        Each acl and role resolves to a list of default or custom actions.
        - Default actions are hard-coded as ["READ", "WRITE"] or ["READ"]
        - Custom actions are configured 'ActionDimensions'

        Args:
            action (RoleType): a supported bootstrap-role, representing a group of actions
            acl_type (str): an acl from 'AclDefaultTypes'

        Returns:
            List[str]: list of action
        """
        return ActionDimensions[action].get(acl_type, ["READ", "WRITE"] if action == RoleType.OWNER else ["READ"])

    def generate_admin_action(self, acl_admin_type):
        return ActionDimensions[RoleType.ADMIN][acl_admin_type]

    def get_ns_node_shared_access_by_name(self, node_name) -> SharedAccess:
        for ns in self.bootstrap_config.namespaces:
            for ns_node in ns.ns_nodes:
                if node_name == ns_node.node_name:
                    return ns_node.shared_access
        return SharedAccess(owner=[], read=[])

    def get_raw_dbs_groupedby_action(self, action, ns_name, node_name=None):
        raw_db_names: Dict[str, Any] = {RoleType.OWNER: [], RoleType.READ: []}
        if node_name:
            raw_db_names[action].extend(
                # the dataset which belongs directly to this node_name
                [
                    self.get_raw_dbs_name_template().format(node_name=node_name, raw_variant=raw_variant)
                    for raw_variant in CommandBase.RAW_VARIANTS
                ]
            )

            # for owner groups add "shared_owner_access" raw_dbs too
            if action == RoleType.OWNER:
                raw_db_names[RoleType.OWNER].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_node.node_name, raw_variant=raw_variant
                        )
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).owner
                        for raw_variant in CommandBase.RAW_VARIANTS
                    ]
                )
                raw_db_names[RoleType.READ].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_node.node_name, raw_variant=raw_variant
                        )
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).read
                        for raw_variant in CommandBase.RAW_VARIANTS
                    ]
                )

        else:  # handling the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME}
            raw_db_names[action].extend(
                [
                    self.get_raw_dbs_name_template().format(node_name=ns_node.node_name, raw_variant=raw_variant)
                    for ns in self.bootstrap_config.namespaces
                    if ns.ns_name == ns_name
                    for ns_node in ns.ns_nodes
                    for raw_variant in CommandBase.RAW_VARIANTS
                ]
                # adding the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME} rawdbs
                + [  # noqa
                    self.get_raw_dbs_name_template().format(
                        node_name=self.get_allprojects_name_template(ns_name=ns_name), raw_variant=raw_variant
                    )
                    for raw_variant in CommandBase.RAW_VARIANTS
                ]
            )
            # only owner-groups support "shared_access" rawdbs
            if action == RoleType.OWNER:
                raw_db_names[RoleType.OWNER].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_access_node.node_name, raw_variant=raw_variant
                        )
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.owner
                        for raw_variant in CommandBase.RAW_VARIANTS
                    ]
                )
                raw_db_names[RoleType.READ].extend(
                    [
                        self.get_raw_dbs_name_template().format(
                            node_name=shared_access_node.node_name, raw_variant=raw_variant
                        )
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.read
                        for raw_variant in CommandBase.RAW_VARIANTS
                    ]
                )

        # returns clear names grouped by action
        return raw_db_names

    def get_spaces_groupedby_action(self, action, ns_name, node_name=None):
        spaces_by_action: Dict[str, Any] = {RoleType.OWNER: [], RoleType.READ: []}
        # for example fac:001:wasit, uc:002:meg, etc.
        if node_name:
            spaces_by_action[action].extend(
                # the dataset which belongs directly to this node_name
                [self.get_space_name_template(node_name=node_name)]
            )

            # for owner groups add "shared_access" datasets too
            if action == RoleType.OWNER:
                spaces_by_action[RoleType.OWNER].extend(
                    [
                        self.get_space_name_template(node_name=shared_node.node_name)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).owner
                    ]
                )
                spaces_by_action[RoleType.READ].extend(
                    [
                        self.get_space_name_template(node_name=shared_node.node_name)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).read
                    ]
                )
        # for example src, fac, uc, ca
        else:  # handling the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME}
            spaces_by_action[action].extend(
                [
                    # all datasets for each of the nodes of the given namespace
                    self.get_space_name_template(node_name=ns_node.node_name)
                    for ns in self.bootstrap_config.namespaces
                    if ns.ns_name == ns_name
                    for ns_node in ns.ns_nodes
                ]
                # adding the {ns_name}:{BootstrapCore.AGGREGATED_GROUP_NAME} dataset
                + [self.get_space_name_template(node_name=self.get_allprojects_name_template(ns_name=ns_name))]  # noqa
            )
            # only owner-groups support "shared_access" datasets
            if action == RoleType.OWNER:
                spaces_by_action[RoleType.OWNER].extend(
                    [
                        self.get_space_name_template(node_name=shared_access_node.node_name)
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.owner
                    ]
                )
                spaces_by_action[RoleType.READ].extend(
                    [
                        self.get_space_name_template(node_name=shared_access_node.node_name)
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.read
                    ]
                )

        # returns clear names
        return spaces_by_action

    def get_datasets_groupedby_action(self, action: RoleType, ns_name: str, node_name: str = None):
        dataset_names: Dict[str, Any] = {RoleType.OWNER: [], RoleType.READ: []}
        # for example fac:001:wasit, uc:002:meg, etc.
        if node_name:
            dataset_names[action].extend(
                # the dataset which belongs directly to this node_name
                [self.get_dataset_name_template().format(node_name=node_name)]
            )

            # for owner groups add "shared_access" datasets too
            if action == RoleType.OWNER:
                dataset_names[RoleType.OWNER].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_node.node_name)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_node in self.get_ns_node_shared_access_by_name(node_name).owner
                    ]
                )
                dataset_names[RoleType.READ].extend(
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
            if action == RoleType.OWNER:
                dataset_names[RoleType.OWNER].extend(
                    [
                        self.get_dataset_name_template().format(node_name=shared_access_node.node_name)
                        # and check the "shared_access" groups list (else [])
                        for ns in self.bootstrap_config.namespaces
                        if ns.ns_name == ns_name
                        for ns_node in ns.ns_nodes
                        for shared_access_node in ns_node.shared_access.owner
                    ]
                )
                dataset_names[RoleType.READ].extend(
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
        ds_by_action = self.get_datasets_groupedby_action(action, ns_name, node_name)
        spaces_by_action = self.get_spaces_groupedby_action(action, ns_name, node_name)
        rawdbs_by_action = self.get_raw_dbs_groupedby_action(action, ns_name, node_name)
        return {
            action: {
                ScopeCtxType.RAWDB: rawdbs_by_action[action],
                ScopeCtxType.DATASET: ds_by_action[action],
                ScopeCtxType.SPACE: spaces_by_action[action],
            }
            for action in [RoleType.OWNER, RoleType.READ]
        }  # fmt: skip

    def generate_scope(self, acl_type: str, scope_ctx: Dict[ScopeCtxType, List[str]]):

        # first handle acl types **without** scope support:
        if acl_type in AclAllScopeOnlyTypes:
            return {"all": {}}

        # next handle acl types **with** scope support:
        match acl_type:
            case "raw":
                # { "tableScope": { "dbsToTables": { "foo:db": {}, "bar:db": {} } }
                return {"tableScope": {"dbsToTables": {raw: {} for raw in scope_ctx[ScopeCtxType.RAWDB]}}}
            case "dataModels":
                # DMS v2:
                # { "dataModelScope": { "externalIds": [ "foo", "bar" ] }
                # return {"dataModelScope": {"externalIds": [space for space in scope_ctx[ScopeCtxType.SPACE]]}}

                # DMS v3:
                # { "spaceIdScope": { "spaceIds": [ "foo", "bar" ] }
                return {"spaceIdScope": {"spaceIds": [space for space in scope_ctx[ScopeCtxType.SPACE]]}}
            case "dataModelInstances":
                # DMS v2:
                # { "spaceScope": { "externalIds": [ "foo", "bar" ] }
                # return {"spaceScope": {"externalIds": [space for space in scope_ctx[ScopeCtxType.SPACE]]}}

                # DMS v3:
                # { "spaceIdScope": { "spaceIds": [ "foo", "bar" ] }
                return {"spaceIdScope": {"spaceIds": [space for space in scope_ctx[ScopeCtxType.SPACE]]}}
            case "datasets":
                # { "idScope": { "ids": [ 2695894113527579, 4254268848874387 ] } }
                return {"idScope": {"ids": self.dataset_names_to_ids(scope_ctx[ScopeCtxType.DATASET])}}
            case "groups":
                return {"currentuserscope": {}}
            case _:  # like 'assets', 'events', 'files', 'sequences', 'timeSeries', ..
                # { "datasetScope": { "ids": [ 2695894113527579, 4254268848874387 ] } }
                return {"datasetScope": {"ids": self.dataset_names_to_ids(scope_ctx[ScopeCtxType.DATASET])}}

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

        Returns:
            Tuple[str, List[Dict[str, Any]]]: group-name and list of capabilities
        """

        capabilities = []

        # detail level like cdf:src:001:public:read
        if action and ns_name and node_name:
            # group for each dedicated group-core id
            group_name_full_qualified = f"{CommandBase.GROUP_NAME_PREFIX}{node_name}:{action}"

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
                for acl_type in AclDefaultTypes
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(action, ns_name, node_name).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx[ScopeCtxType.RAWDB] and scope_ctx[ScopeCtxType.DATASET]
            ]

        # group-type level like cdf:src:all:read
        elif action and ns_name:
            # 'all' groups on group-type level
            # (access to all datasets/ raw-dbs which belong to this group-type)
            group_name_full_qualified = (
                f"{CommandBase.GROUP_NAME_PREFIX}{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}:{action}"  # noqa
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
                for acl_type in AclDefaultTypes
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(action, ns_name).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx[ScopeCtxType.RAWDB] and scope_ctx[ScopeCtxType.DATASET]
            ]

        # top level like cdf:all:read
        elif action:
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            group_name_full_qualified = f"{CommandBase.GROUP_NAME_PREFIX}{CommandBase.AGGREGATED_LEVEL_NAME}:{action}"

            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action(action, acl_type),
                            # scope = { "all": {} }
                            # create scope for all raw_dbs and datasets
                            scope=self.generate_scope(acl_type, self.all_scoped_ctx),
                        )
                    }
                )
                for acl_type in AclDefaultTypes
            ]

        # root level like cdf:root
        elif root_account:  # no parameters
            # all (no limits)
            group_name_full_qualified = f"{CommandBase.GROUP_NAME_PREFIX}{root_account}"
            # all default ACLs
            [
                capabilities.append(  # type: ignore
                    {
                        f"{acl_type}Acl": self.acl_template(
                            # check for acl specific owner actions, else default
                            actions=self.generate_default_action(RoleType.OWNER, acl_type),
                            scope={"all": {}},
                        )
                    }
                )
                # skipping admin types from default types to avoid duplicates
                for acl_type in (set(AclDefaultTypes) - set(AclAdminTypes))
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
                for acl_admin_type in AclAdminTypes
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
            logging.info(f"Dry run - Creating group with name: <{new_group.name}>")
            logging.debug(f"Dry run - Creating group details: <{new_group}>")
        else:
            logging.debug(f"  creating: {new_group.name} [idp source: {new_group.source_id}]")
            new_group: Union[Group, GroupList] = self.client.iam.groups.create(new_group)
            self.deployed.groups.create(resources=new_group)
            logging.info(f"  {new_group.name} ({new_group.id}) [idp source: {new_group.source_id}]")

        # if the group name existed before, delete those groups now
        # same upsert approach Fusion is using to update a CDF group: create new with changes => then delete old one
        if old_group_ids:
            if self.is_dry_run:
                logging.info(f"Dry run - Deleting groups with ids: <{old_group_ids}>")
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
                    node_name=f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else CommandBase.AGGREGATED_LEVEL_NAME
                ):
                # value
                {
                    "description": f"Dataset for '{CommandBase.AGGREGATED_LEVEL_NAME}' Owner groups",
                    # "metadata": "",
                    "external_id": f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else CommandBase.AGGREGATED_LEVEL_NAME,
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
                logging.info(f"Dry run - Creating missing datasets: {[name for name in missing_datasets]}")
                logging.debug(f"Dry run - Creating missing datasets (details): <{datasets_to_be_created}>")
            else:
                created_datasets: Union[DataSet, DataSetList] = self.client.data_sets.create(datasets_to_be_created)
                self.deployed.datasets.create(resources=created_datasets)

        # which targets are already deployed?
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
                logging.info(f"Dry run - Updating existing datasets: {[name for name in existing_datasets]}")
                # dump of DataSetUpdate object
                logging.debug(f"Dry run - Updating existing datasets (details): <{datasets_to_be_updated}>")
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
                for raw_variant in CommandBase.RAW_VARIANTS
            ]
        )
        target_raw_db_names.update(
            # add RAW DBs for 'all' users
            [
                self.get_raw_dbs_name_template().format(
                    node_name=f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else CommandBase.AGGREGATED_LEVEL_NAME,
                    raw_variant=raw_variant,
                )
                # creating allprojects at group type level + top-level
                for ns_name in list([ns.ns_name for ns in self.bootstrap_config.namespaces]) + [""]
                for raw_variant in CommandBase.RAW_VARIANTS
            ]
        )

        return target_raw_db_names

    def generate_missing_raw_dbs(self) -> Tuple[List[str], List[str]]:
        target_raw_db_names = self.generate_target_raw_dbs()

        try:
            # which targets are not already deployed?
            missing_rawdb_names = target_raw_db_names - set(self.deployed.raw_dbs.get_names())
        except Exception as exc:
            logging.info(f"RAW databases do not exist in CDF:\n{exc}")
            missing_rawdb_names = target_raw_db_names

        if missing_rawdb_names:
            # create all raw_dbs which are not already deployed
            if self.is_dry_run:
                for raw_db in list(missing_rawdb_names):
                    logging.info(f"Dry run - Creating rawdb: <{raw_db}>")
            else:
                created_rawdbs: Union[Database, DatabaseList] = self.client.raw.databases.create(
                    list(missing_rawdb_names)
                )
                self.deployed.raw_dbs.create(resources=created_rawdbs)

        return target_raw_db_names, missing_rawdb_names

    def generate_target_spaces(self) -> Set[str]:
        # list of all targets: autogenerated space names
        target_space_names = set(
            [
                self.get_space_name_template(node_name=ns_node.node_name)
                for ns in self.bootstrap_config.namespaces
                for ns_node in ns.ns_nodes
            ]
        )
        target_space_names.update(
            # add SPACEs for 'all' users
            [
                self.get_space_name_template(
                    node_name=f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}"
                    if ns_name
                    else CommandBase.AGGREGATED_LEVEL_NAME,
                )
                # creating allprojects at group type level + top-level
                for ns_name in list([ns.ns_name for ns in self.bootstrap_config.namespaces]) + [""]
            ]
        )

        return target_space_names

    def generate_missing_spaces(self) -> Tuple[List[str], List[str]]:
        target_space_names = self.generate_target_spaces()

        try:
            # which targets are not already deployed?
            missing_space_names = target_space_names - set(self.deployed.spaces.get_names())
        except Exception as exc:
            logging.info(f"RAW databases do not exist in CDF:\n{exc}")
            missing_space_names = target_space_names

        if missing_space_names:
            # v2
            # spaces_to_be_created = [DataModelStorageSpace(external_id=name) for name in missing_space_names]
            # v3
            spaces_to_be_created = [ModelsSpace(space=name, name=name) for name in missing_space_names]
            # create all spaces which are not already deployed
            if self.is_dry_run:
                for space in list(missing_space_names):
                    logging.info(f"Dry run - Creating space: <{space}>")
            else:
                # v2
                # created_spaces: Union[
                #     DataModelStorageSpace, DataModelStorageSpaceList
                # ] = self.client.data_model_storages.spaces.create(space=spaces_to_be_created)
                # v3
                created_spaces: Union[ModelsSpace, ModelsSpaceList] = self.client.models.spaces.create(
                    space=spaces_to_be_created
                )
                self.deployed.spaces.create(resources=created_spaces)

        return target_space_names, missing_space_names

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
        logging.info(f"Generating special groups:\n{special_group_names}")

        for special_group_name in special_group_names:
            self.create_group(group_name=special_group_name)

    # generate all groups - iterating through the 3-level hierarchy
    def generate_groups(self):
        # permutate the combinations
        for action in [RoleType.READ, RoleType.OWNER]:  # ActionDimensions w/o 'admin'
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
                    f"{ScopeCtxType.RAWDB}": [],
                    f"{ScopeCtxType.DATASET}": [],
                    f"{ScopeCtxType.SPACE}": [],
                    f"{ScopeCtxType.GROUP}": [],
                },
                "latest_deployment": {
                    f"{ScopeCtxType.RAWDB}": sorted(self.deployed.raw_dbs.get_names()),
                    # (.. or "") because dataset names can be empty (None value)
                    f"{ScopeCtxType.DATASET}": sorted(self.deployed.datasets.get_names()),
                    f"{ScopeCtxType.SPACE}": sorted(self.deployed.spaces.get_names()),
                    # (.. or "") because group names can be empty (None value)
                    f"{ScopeCtxType.GROUP}": sorted(self.deployed.groups.get_names()),
                },
            }
        )
        logging.info(f"Delete template:\n{delete_template}")
        # return delete_template
