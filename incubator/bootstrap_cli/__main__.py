"""
Changelog:
210504 mh:
 * Adding support for minimum groups and project capabilities for read and owner Groups
 * Exception handling for root-groups to avoid duplicate groups and projects capabilities
210610 mh:
 * Adding RAW DBs and Datasets for Groups {env}:allprojects:{owner/read} and {env}:{group}:allprojects:{owner/read}
 * Adding functionality for updating dataset details (external id, description, etc) based on the config.yml
210910 pa:
 * extended acl_default_types by labels, relationships, functions
 * removed labels from acl_admin_types
 * functions don't have dataset scope
211013 pa:
 * renamed "adfs" to "aad" terminology => aad_mappings
 * for AAD 'root:client' and 'root:user' can be merged into 'root'
211014 pa:
 * adding new capabilities
      extractionpipelinesAcl
      extractionrunsAcl
211108 pa:
 * adding new capabilities
      entitymatchingAcl
 * refactor list of acl types which only support "all" scope
      acl_all_scope_only_types
 * support "labels" for non admin groups
211110 pa:
 * adding new capabilities
      sessionsAcl
220202 pa:
 * adding new capabilities
      typesAcl
220216 pa:
 * adding 'generate_special_groups()' to handle
   'extractors' and 'transformations' and their 'aad_mappings'
   * configurable through `deploy --with-special-groups=[yes|no]` parameter
 * adding new capabilities:
      transformationsAcl (replacing the need for magic "transformations" CDF Group)

"""
# std-lib
import logging
import time
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from itertools import islice
from pathlib import Path

# type-hints
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# 3rd party libs
import pandas as pd

# cli
import click
from click import Context

# Cognite Python SDK and Utils support
from cognite.client import CogniteClient

# using extractor-utils instead of native CogniteClient
from cognite.client.data_classes import DataSet, Group
from cognite.client.data_classes.data_sets import DataSetUpdate
from cognite.extractorutils.configtools import CogniteConfig, LoggingConfig, load_yaml
from dotenv import load_dotenv

# cli internal
from incubator.bootstrap_cli import __version__

# import getpass
_logger = logging.getLogger(__name__)
#
# LOAD configs
#


# mixin 'str' to 'Enum' to support comparison to string-values
# https://docs.python.org/3/library/enum.html#others
# https://stackoverflow.com/a/63028809/1104502
class YesNoType(str, Enum):
    yes = "yes"
    no = "no"


@dataclass
class BootstrapBaseConfig:
    logger: LoggingConfig
    cognite: CogniteConfig
    # token_custom_args: Dict[str, Any]
    # TODO: ading default_factory value, will break the code
    # or you have to apply for all *following* fields, default values too
    # see https://stackoverflow.com/q/51575931/1104502
    # https://medium.com/@aniscampos/python-dataclass-inheritance-finally-686eaf60fbb5
    token_custom_args: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, filepath):
        try:
            with open(filepath) as file:
                return load_yaml(source=file, config_type=cls)
        except FileNotFoundError as exc:
            print("Incorrect file path, error message: ", exc)
            raise


@dataclass
class BootstrapDeployConfig(BootstrapBaseConfig):
    """
    Configuration parameters for CDF Project Bootstrap, deploy(create) & prepare mode
    """

    bootstrap: Dict[str, Any] = field(default_factory=dict)
    aad_mappings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BootstrapDeleteConfig(BootstrapBaseConfig):
    """
    Configuration parameters for CDF Project Bootstrap, delete mode
    """

    delete_or_deprecate: Dict[str, Any] = field(default_factory=dict)


class BootstrapConfigError(Exception):
    """Exception raised for config parser

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


#
# GENERIC configurations
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
]

acl_admin_types = [
    "projects",
    "groups",
]

# this acls only support "all": {} scope
acl_all_scope_only_types = set(["projects", "sessions", "functions", "entitymatching", "transformations", "types"])

action_dimensions = {
    # owner datasets might only need READ and OWNER
    "owner": {
        "raw": ["READ", "WRITE", "LIST"],
        "datasets": ["READ", "WRITE", "OWNER"],
        "groups": ["LIST"],
        "projects": ["LIST"],
        "sessions": ["LIST", "CREATE"],
    },  # else ["READ","WRITE"]
    "read": {"raw": ["READ", "LIST"], "groups": ["LIST"], "projects": ["LIST"], "sessions": ["LIST"]},  # else ["READ"]
    "admin": {
        "groups": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"],
        "projects": ["READ", "UPDATE", "LIST"],
    },
}


class BootstrapCore:

    # 210330 pa: all rawdbs come in two variants `:rawdb` and `:rawdb:state`
    RAW_SUFFIXES = ["", ":state"]

    # Mark all auto-generated CDF Group names
    GROUP_NAME_PREFIX = "cdf:"

    def __init__(self, configpath: str, delete: bool = False):
        if delete:
            self.config: BootstrapDeleteConfig = BootstrapDeleteConfig.from_yaml(configpath)
            self.delete_or_deprecate: Dict[str, Any] = self.config.delete_or_deprecate
        else:
            self.config: BootstrapDeployConfig = BootstrapDeployConfig.from_yaml(configpath)
            self.group_types_dimensions: Dict[str, Any] = self.config.bootstrap
            self.aad_mapping_lookup: Dict[str, Any] = self.config.aad_mappings

        self.deployed: Dict[str, Any] = {}
        self.all_scope_ctx: Dict[str, Any] = {}

        # TODO debug
        # print(f"self.config= {self.config}")

        # make sure the optional folders in logger.file.path exists
        # to avoid: FileNotFoundError: [Errno 2] No such file or directory: '/github/workspace/logs/test-deploy.log'

        if self.config.logger.file:
            (Path.cwd() / self.config.logger.file.path).parent.mkdir(parents=True, exist_ok=True)

        self.config.logger.setup_logging()

        _logger.info("Starting CDF Bootstrap configuration")

        self.client: CogniteClient = self.config.cognite.get_cognite_client(  # noqa
            client_name="inso-bootstrap-cli", token_custom_args=self.config.token_custom_args
        )

        _logger.info("Successful connection to CDF client")

    @staticmethod
    def acl_template(actions, scope):
        return {"actions": actions, "scope": scope}

    @staticmethod
    def get_allprojects_name_template(group_type=None):
        return f"{group_type}:allprojects" if group_type else "allprojects"

    @staticmethod
    def get_dataset_name_template():
        # 211013 pa: remove env prefixes
        # return f"{shared_global_config['env']}:" + "{group_prefix}:dataset"
        return "{group_prefix}:dataset"

    @staticmethod
    def get_raw_dbs_name_template():
        # 211013 pa: remove env prefixes
        # return f"{shared_global_config['env']}:" + "{group_prefix}:rawdb{raw_suffix}"
        return "{group_prefix}:rawdb{raw_suffix}"

    # 211013 pa: remove env prefixes
    # def add_prefix_external_id(external_id):
    #     # only prefix dataset external id with environment if 'prefix_external_id flag' is set to true in the config
    #     if prefix_external_id:
    #         return f"{shared_global_config['env']}:{external_id}"
    #     else:
    #         return external_id
    @staticmethod
    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_default_action(self, action, acl_type):
        return action_dimensions[action].get(acl_type, ["READ", "WRITE"] if action == "owner" else ["READ"])

    def generate_admin_action(self, acl_admin_type):
        return action_dimensions["admin"][acl_admin_type]

    def get_group_config_by_name(self, group_prefix):
        for group_type, group_configs in self.group_types_dimensions.items():
            if group_prefix in group_configs:
                return group_configs[group_prefix]

    def get_group_raw_dbs_groupedby_action(self, action, group_type, group_prefix=None):
        raw_db_names: Dict[str, Any] = {"owner": [], "read": []}
        if group_prefix:
            raw_db_names[action].extend(
                # the dataset which belongs directly to this group_prefix
                [
                    self.get_raw_dbs_name_template().format(group_prefix=group_prefix, raw_suffix=raw_suffix)
                    for raw_suffix in BootstrapCore.RAW_SUFFIXES
                ]
            )

            # for owner groups add "shared_owner_access" raw_dbs too
            if action == "owner":
                raw_db_names["owner"].extend(
                    [
                        self.get_raw_dbs_name_template().format(group_prefix=shared_access, raw_suffix=raw_suffix)
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_access in self.get_group_config_by_name(group_prefix).get("shared_owner_access", [])
                        for raw_suffix in BootstrapCore.RAW_SUFFIXES
                    ]
                )
                raw_db_names["read"].extend(
                    [
                        self.get_raw_dbs_name_template().format(group_prefix=shared_access, raw_suffix=raw_suffix)
                        # find the group_config which matches the name,
                        # and check the "shared_access" groups list (else [])
                        for shared_access in self.get_group_config_by_name(group_prefix).get("shared_read_access", [])
                        for raw_suffix in BootstrapCore.RAW_SUFFIXES
                    ]
                )

        else:  # handling the {group_type}:allprojects
            raw_db_names[action].extend(
                [
                    self.get_raw_dbs_name_template().format(group_prefix=group_prefix, raw_suffix=raw_suffix)
                    for group_prefix, group_config in self.group_types_dimensions[group_type].items()
                    for raw_suffix in BootstrapCore.RAW_SUFFIXES
                ]
                # adding the {group_type}:allprojects rawdbs
                + [  # noqa
                    self.get_raw_dbs_name_template().format(
                        group_prefix=self.get_allprojects_name_template(group_type=group_type), raw_suffix=raw_suffix
                    )
                    for raw_suffix in BootstrapCore.RAW_SUFFIXES
                ]
            )
            # for owner groups add "shared_owner_access" raw_dbs too
            if action == "owner":
                raw_db_names["owner"].extend(
                    [
                        self.get_raw_dbs_name_template().format(group_prefix=shared_access, raw_suffix=raw_suffix)
                        # and check the "shared_access" groups list (else [])
                        for _, group_config in self.group_types_dimensions[group_type].items()
                        for shared_access in group_config.get("shared_owner_access", [])
                        for raw_suffix in BootstrapCore.RAW_SUFFIXES
                    ]
                )
                raw_db_names["read"].extend(
                    [
                        self.get_raw_dbs_name_template().format(group_prefix=shared_access, raw_suffix=raw_suffix)
                        # and check the "shared_access" groups list (else [])
                        for _, group_config in self.group_types_dimensions[group_type].items()
                        for shared_access in group_config.get("shared_read_access", [])
                        for raw_suffix in BootstrapCore.RAW_SUFFIXES
                    ]
                )

        # returns clear names grouped by action
        return raw_db_names

    def get_group_datasets_groupedby_action(self, action, group_type, group_prefix=None):
        dataset_names: Dict[str, Any] = {"owner": [], "read": []}
        # for example fac:001:wasit, uc:002:meg, etc.
        if group_prefix:
            dataset_names[action].extend(
                # the dataset which belongs directly to this group_prefix
                [self.get_dataset_name_template().format(group_prefix=group_prefix)]
            )

            # for owner groups add "shared_access" datasets too
            if action == "owner":
                dataset_names["owner"].extend(
                    [
                        self.get_dataset_name_template().format(group_prefix=shared_access)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_access in self.get_group_config_by_name(group_prefix).get("shared_owner_access", [])
                    ]
                )
                dataset_names["read"].extend(
                    [
                        self.get_dataset_name_template().format(group_prefix=shared_access)
                        # find the group_config which matches the id,
                        # and check the "shared_access" groups list (else [])
                        for shared_access in self.get_group_config_by_name(group_prefix).get("shared_read_access", [])
                    ]
                )
        # for example fac, uc, ca
        else:  # handling the {group_type}:allprojects
            dataset_names[action].extend(
                [
                    self.get_dataset_name_template().format(group_prefix=group_prefix)
                    for group_prefix, group_config in self.group_types_dimensions[group_type].items()
                ]
                # adding the {group_type}:allprojects dataset
                + [  # noqa
                    self.get_dataset_name_template().format(
                        group_prefix=self.get_allprojects_name_template(group_type=group_type)
                    )
                ]
            )
            # for owner groups add "shared_access" datasets too
            if action == "owner":
                dataset_names["owner"].extend(
                    [
                        self.get_dataset_name_template().format(group_prefix=shared_access)
                        # and check the "shared_access" groups list (else [])
                        for _, group_config in self.group_types_dimensions[group_type].items()
                        for shared_access in group_config.get("shared_owner_access", [])
                    ]
                )
                dataset_names["read"].extend(
                    [
                        self.get_dataset_name_template().format(group_prefix=shared_access)
                        # and check the "shared_access" groups list (else [])
                        for _, group_config in self.group_types_dimensions[group_type].items()
                        for shared_access in group_config.get("shared_read_access", [])
                    ]
                )

        # returns clear names
        return dataset_names

    def dataset_names_to_ids(self, dataset_names):
        return self.deployed["datasets"].query("name in @dataset_names")["id"].tolist()

    def get_scope_ctx_groupedby_action(self, action, group_type, group_prefix=None):
        ds_by_action = self.get_group_datasets_groupedby_action(action, group_type, group_prefix)
        rawdbs_by_action = self.get_group_raw_dbs_groupedby_action(action, group_type, group_prefix)
        # regroup to get action as main key
        # {action : scope_ctx}
        return {
            action: {"raw": rawdbs_by_action[action], "datasets": ds_by_action[action]} for action in ["owner", "read"]
        }

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

    def generate_group_name_and_capabilities(self, action=None, group_type=None, group_prefix=None, root_account=None):
        capabilities = []

        # detail level like cdf:src:001:public:read
        if action and group_type and group_prefix:
            # group for each dedicated group-type id
            # group_name_full_qualified = f"{shared_global_config['env']}:{group_prefix}:{action}"
            group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{group_prefix}:{action}"

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
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(
                    action, group_type, group_prefix
                ).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx["raw"] and scope_ctx["datasets"]
            ]

        # group-type level like cdf:src:allprojects:read
        elif action and group_type:
            # 'allprojects' groups on group-type level
            # (access to all datasets/ raw-dbs which belong to this group-type)
            # group_name_full_qualified = f"{shared_global_config['env']}:{group_type}:allprojects:{action}"
            group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}{group_type}:allprojects:{action}"

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
                for shared_action, scope_ctx in self.get_scope_ctx_groupedby_action(action, group_type).items()
                # don't create empty scopes
                # enough to check one as they have both same length, but that's more explicit
                if scope_ctx["raw"] and scope_ctx["datasets"]
            ]

        # top level like cdf:allprojects:read
        elif action:
            # 'allprojects' groups on action level (no limits to datasets or raw-dbs)
            # group_name_full_qualified = f"{shared_global_config['env']}:allprojects:{action}"
            group_name_full_qualified = f"{BootstrapCore.GROUP_NAME_PREFIX}allprojects:{action}"

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
            # group_name_full_qualified = f"{shared_global_config['env']}:{root_account}"
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
        """Lookup if CDF Group name exists (could be more than one!)
        and return list of all CDF Group IDs

        Args:
            group_name (str): CDF Group name to check

        Returns:
            List[int]: of CDF Group IDs
        """

        return self.deployed["groups"].query("name == @group_name")["id"].tolist()

        # return self.deployed["groups"].query("name == @group_payload['name']")["id"].tolist()
        # TODO 220203 pa: explicit providing 'group_name'
        #     to bypass a strange bug under Docker which throws a
        #     pandas.core.computation.ops.UndefinedVariableError:
        #       name 'str_0_0x900xd80x90xec0x870x7f0x00x0' is not defined

    def create_group(
        self, group_name: str, group_capabilities: Dict[str, Any] = None, aad_mapping: Tuple[str] = None
    ) -> Group:
        """Creating a CDF Group
        - with upsert support the same way Fusion updates CDF Groups
          if a group with the same name exists:
              1. a new group with the same name will be created
              2. then the old group will be deleted (by its 'id')
        - with support of explicit given aad-mapping or internal lookup from config

        Args:
            group_name (str): name of the CDF Group, always prefixed with GROUP_NAME_PREFIX
            group_capabilities (Dict[str, Any], optional): Defining te CDF Group capabilities.
            aad_mapping (Tuple(str), optional): one pair of (AAD SourceID, AAD SourceName),
                to link the CDF Group to

        Returns:
            Group: the new created CDF Group
        """

        aad_source_id, aad_source_name = None, None
        if aad_mapping:
            # explicit given
            # TODO: change from tuple to dataclass
            assert len(aad_mapping) == 2
            aad_source_id, aad_source_name = aad_mapping
        else:
            # check lookup from provided config
            aad_source_id, aad_source_name = self.aad_mapping_lookup.get(group_name, [None, None])

        # print(f"=====  group_name<{group_name}> | aad_source_id<{aad_source_id}>
        # | aad_source_name<{aad_source_name}> ===")

        # check if group already exists, if yes it will be deleted after a new one is created
        old_group_ids = self.get_group_ids_by_name(group_name)

        new_group = Group(name=group_name, capabilities=group_capabilities)
        if aad_source_id:
            # inject (both will be pushed through the API call!)
            new_group.source_id = aad_source_id  # 'S-314159-1234'
            new_group.source = aad_source_name  # type: ignore # 'AD Group FooBar' # type: ignore

        # print(f"group_create_object:<{group_create_object}>")
        # overwrite new_group as it now contains id too
        new_group = self.client.iam.groups.create(new_group)

        # if the group name existed before, delete those groups now
        # same upsert approach Fusion is using to update a CDF Group: create new with changes => then delete old one
        if old_group_ids:
            self.client.iam.groups.delete(old_group_ids)

        return new_group

    def process_group(self, action=None, group_type=None, group_prefix=None, root_account=None):
        # to avoid complex upsert logic, all groups will be recreated and then the old ones deleted

        # to be merged with existing code
        # print(f"=== START: action<{action}> | group_type<{group_type}> | group_prefix<{group_prefix}> ===")

        group_name, group_capabilities = self.generate_group_name_and_capabilities(
            action, group_type, group_prefix, root_account
        )

        return self.create_group(group_name, group_capabilities)

    def generate_missing_datasets(self) -> Tuple[List[str], List[str]]:
        # list of all targets: autogenerated dataset names
        target_datasets = {
            # dictionary generator
            # dataset_name : {Optional[dataset_description], Optional[dataset_metadata], ..}
            # key:
            self.get_dataset_name_template().format(group_prefix=group_prefix):
            # value
            {
                "description": group_config.get("description"),
                "metadata": group_config.get("metadata"),
                # "external_id": add_prefix_external_id(group_config.get("external_id")),
                "external_id": group_config.get("external_id"),
            }
            for group_type, group_configs in self.group_types_dimensions.items()
            for group_prefix, group_config in group_configs.items()
        }

        # update target datasets to include 'allproject' and '{group_type}:allprojects' datasets
        target_datasets.update(
            {  # dictionary generator
                # key:
                self.get_dataset_name_template().format(
                    group_prefix=f"{group_type}:allprojects" if group_type else "allprojects"
                ):
                # value
                {
                    "description": "Dataset for 'allprojects' Owner Groups",
                    # "metadata": "",
                    # "external_id": add_prefix_external_id(
                    #     f"{group_type}:allprojects" if group_type else "allprojects"
                    # ),  # without env prefix
                    "external_id": f"{group_type}:allprojects" if group_type else "allprojects",
                }
                # creating allprojects at group type level + top-level
                for group_type in list(self.group_types_dimensions.keys()) + [""]
            }
        )

        # TODO check chunking options from SDK
        def chunks(data, SIZE=10000):
            it = iter(data)
            for i in range(0, len(data), SIZE):
                yield {k: data[k] for k in islice(it, SIZE)}

        # which targets are not already deployed?
        missing_datasets = {
            name: payload
            for name, payload in target_datasets.items()
            if name not in self.deployed["datasets"]["name"].tolist()
        }

        if missing_datasets:
            # create all datasets which are not already deployed
            # https://docs.cognite.com/api/v1/#operation/createDataSets
            # xxx TBD: description, metadata, externalId
            for chunked_missing_datasets in chunks(missing_datasets, 10):
                self.client.data_sets.create(
                    [
                        DataSet(
                            name=name,
                            description=payload.get("description"),
                            # external_id=add_prefix_external_id(payload.get("external_id")),
                            external_id=payload.get("external_id"),
                            metadata=payload.get("metadata"),
                            write_protected=True,
                        )
                        for name, payload in chunked_missing_datasets.items()
                    ]
                )

        # which targets are already deployed?
        existing_datasets = {
            # dictionary generator
            # key:
            dataset_columns["name"]:
            # value
            # Merge dataset 'id' from CDF with dataset arguments from config.yml
            dict(id=dataset_columns["id"], **target_datasets[dataset_columns["name"]])
            for row_id, dataset_columns in self.deployed["datasets"].iterrows()  # iterating pd dataframe
            if dataset_columns["name"] in target_datasets.keys()
        }

        if existing_datasets:
            # update datasets which are already deployed
            # https://docs.cognite.com/api/v1/#operation/createDataSets
            # TODO: description, metadata, externalId
            for chunked_existing_datasets in chunks(existing_datasets, 10):
                self.client.data_sets.update(
                    [
                        DataSetUpdate(id=dataset["id"])
                        .name.set(name)
                        .description.set(dataset.get("description"))
                        .external_id.set(dataset.get("external_id"))
                        .metadata.set(dataset.get("metadata"))
                        for name, dataset in chunked_existing_datasets.items()
                    ]
                )
        return list(target_datasets.keys()), list(missing_datasets.keys())

    def generate_missing_raw_dbs(self) -> Tuple[List[str], List[str]]:
        # list of all targets: autogenerated raw_db names
        target_raw_db_names = set(
            [
                self.get_raw_dbs_name_template().format(group_prefix=group_prefix, raw_suffix=raw_suffix)
                for group_type, group_configs in self.group_types_dimensions.items()
                for group_prefix, group_config in group_configs.items()
                for raw_suffix in BootstrapCore.RAW_SUFFIXES
            ]
        )
        target_raw_db_names.update(
            # add RAW DBs for 'allprojects' users
            [
                self.get_raw_dbs_name_template().format(
                    group_prefix=f"{group_type}:allprojects" if group_type else "allprojects", raw_suffix=raw_suffix
                )
                # creating allprojects at group type level + top-level
                for group_type in list(self.group_types_dimensions.keys()) + [""]
                for raw_suffix in BootstrapCore.RAW_SUFFIXES
            ]
        )
        try:
            # which targets are not already deployed?
            missing_rawdbs = target_raw_db_names - set(self.deployed["raw_dbs"]["name"])
        except Exception as exc:
            _logger.info(f"Raw databases do not exist in CDF:\n{exc}")
            missing_rawdbs = target_raw_db_names

        if missing_rawdbs:
            # create all raw_dbs which are not already deployed
            self.client.raw.databases.create(list(missing_rawdbs))

        return target_raw_db_names, missing_rawdbs

    """
    "Special CDF Groups" are groups which don't have capabilities but have an effect by their name only.
    1. 'transformations' group: grants access to "Fusion > Integrate > Transformations"
    2. 'extractors' group: grants access to "Fusion > Integrate > Extract Data" which allows dowload of extractors

    Both of them are about getting deprecated in the future.
    - 'transformations' can already be replaced with proper 'transformationsAcl' capabilities
    """

    def generate_special_groups(self):

        special_group_names = ["extractors", "transformations"]
        _logger.info(f"Generating special groups:\n{special_group_names}")

        for special_group_name in special_group_names:
            self.create_group(group_name=special_group_name)

    # generate all groups
    def generate_groups(self):
        # permutate the combinations
        for action in ["read", "owner"]:  # action_dimensions w/o 'admin'
            for group_type, group_configs in self.group_types_dimensions.items():
                for group_prefix, group_config in group_configs.items():
                    # group for each dedicated group-type id
                    self.process_group(action, group_type, group_prefix)
                # 'allprojects' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                self.process_group(action, group_type)
            # 'allprojects' groups on action level (no limits to datasets or raw-dbs)
            self.process_group(action)
        # all (no limits + admin)
        # 211013 pa: for AAD root:client and root:user can be merged into 'root'
        # for root_account in ["root:client", "root:user"]:
        for root_account in ["root"]:
            self.process_group(root_account=root_account)

    def load_deployed_config_from_cdf(self) -> None:
        NOLIMIT = -1
        # KeyError: "None of [Index(['name', 'id'], dtype='object')] are in the [columns]"
        datasets = self.client.data_sets.list(limit=NOLIMIT).to_pandas()
        if len(datasets) == 0:
            # create an empty dataframe
            datasets = pd.DataFrame(columns=["name", "id"])
        else:
            datasets = datasets[["name", "id"]]
        # datasets = pd.DataFrame()
        raw_list = [
            column for column in self.client.raw.databases.list(limit=NOLIMIT).to_pandas().columns if column in ["name"]
        ]
        columns_list = [
            column
            for column in self.client.iam.groups.list(all=True).to_pandas().columns
            if column in ["name", "id", "sourceId", "capabilities"]
        ]
        self.deployed = {
            "groups": self.client.iam.groups.list(all=True).to_pandas()[columns_list],
            "datasets": datasets,
            "raw_dbs": self.client.raw.databases.list(limit=NOLIMIT).to_pandas()[raw_list],
        }

    # prepare a yaml for "delete" job
    def dump_delete_template_to_yaml(self) -> None:
        # and reload again now with latest group config too

        time.sleep(5)  # wait for groups to be created!
        self.load_deployed_config_from_cdf()

        delete_template = yaml.dump(
            {
                "delete_or_deprecate": {
                    "raw_dbs": [],
                    "datasets": [],
                    "groups": [],
                },
                "latest_deployment": {
                    "raw_dbs": sorted(self.deployed["raw_dbs"].sort_values(["name"])["name"].tolist()),
                    "datasets": sorted(self.deployed["datasets"].sort_values(["name"])["name"].tolist()),
                    "groups": sorted(self.deployed["groups"].sort_values(["name"])["name"].tolist()),
                },
                "dataset_ids": {
                    row["name"]: row["id"] for i, row in sorted(self.deployed["datasets"][["name", "id"]].iterrows())
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

    def prepare(self):
        group_name = "cdf:bootstrap"
        # group_name = f"{create_config.environment}:bootstrap"

        group_capabilities = [
            {"datasetsAcl": {"actions": ["READ", "WRITE", "OWNER"], "scope": {"all": {}}}},
            {"rawAcl": {"actions": ["READ", "WRITE", "LIST"], "scope": {"all": {}}}},
            {"groupsAcl": {"actions": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"], "scope": {"all": {}}}},
            {"projectsAcl": {"actions": ["READ", "UPDATE"], "scope": {"all": {}}}},
        ]

        # TODO: replace with dataclass
        aad_mapping = [
            # sourceId
            (source_id := self.config.cognite.idp_authentication.client_id),
            # sourceName
            f"AAD Server Application: {source_id}",
        ]

        # allows idempotent creates, as it cleans up old groups with same names after creation
        self.create_group(group_name=group_name, group_capabilities=group_capabilities, aad_mapping=aad_mapping)

        _logger.info(f"Created CDF Group {group_name}")
        _logger.info("Finished CDF Project Bootstrapper in 'prepare' mode ")

    def delete(self):
        # load deployed groups, datasets, raw_dbs with their ids and metadata
        self.load_deployed_config_from_cdf()

        # groups
        group_names = self.delete_or_deprecate["groups"]
        if group_names:
            delete_group_ids = self.deployed["groups"].query("name in @group_names")["id"].tolist()
            if delete_group_ids:
                # only delete groups which exist
                _logger.info(f"DELETE groups: {group_names}")
                self.client.iam.groups.delete(delete_group_ids)
            else:
                _logger.info(f"Groups already deleted: {group_names}")
        else:
            _logger.info("No Groups to delete")

        # raw_dbs
        raw_db_names = self.delete_or_deprecate["raw_dbs"]
        if raw_db_names:
            delete_raw_db_names = list(set(raw_db_names).intersection(set(self.deployed["raw_dbs"]["name"])))
            if delete_raw_db_names:
                # only delete dbs which exist
                # print("DELETE raw_dbs recursive with tables: ", raw_db_names)
                _logger.info(f"DELETE raw_dbs recursive with tables: {raw_db_names}")
                self.client.raw.databases.delete(delete_raw_db_names, recursive=True)
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
            delete_datasets_df = self.deployed["datasets"].query("name in @dataset_names")
            if not delete_datasets_df.empty:
                for i, row in delete_datasets_df.iterrows():
                    _logger.info(f"DEPRECATE dataset: {row['name']}")
                    update_dataset = self.client.data_sets.retrieve(id=row["id"])
                    update_dataset.name = (
                        f"_DEPR_{update_dataset.name}"
                        if not update_dataset.name.startswith("_DEPR_")
                        else f"{update_dataset.name}"
                    )  # don't stack the DEPR prefixes
                    update_dataset.description = "Deprecated {}".format(self.get_timestamp())
                    update_dataset.metadata = dict(update_dataset.metadata, archived=True)  # or dict(a, **b)
                    update_dataset.external_id = (
                        # f"_DEPR_{add_prefix_external_id(update_dataset.external_id)}_[{get_timestamp()}]"
                        f"_DEPR_{update_dataset.external_id}_[{self.get_timestamp()}]"
                    )
                    self.client.data_sets.update(update_dataset)
        else:
            _logger.info("No Datasets to archive (and mark as deprecated)")

        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        self.dump_delete_template_to_yaml()
        # TODO: write to file or standard output
        _logger.info("Finished creating CDF Groups, Datasets and RAW Databases")

    def deploy(self, with_special_groups: YesNoType = YesNoType.no):

        # load deployed groups, datasets, raw_dbs with their ids and metadata
        self.load_deployed_config_from_cdf()
        _logger.debug(f"RAW_DBS in CDF:\n{self.deployed['raw_dbs']}")
        _logger.debug(f"DATASETS in CDF:\n{self.deployed['datasets']}")
        _logger.debug(f"GROUPS in CDF:\n{self.deployed['groups']}")

        # run generate steps (only print results atm)
        target_raw_dbs, new_created_raw_dbs = self.generate_missing_raw_dbs()
        _logger.info(f"All RAW_DBS from config:\n{target_raw_dbs}")
        _logger.info(f"New RAW_DBS to CDF:\n{new_created_raw_dbs}")
        target_datasets, new_created_datasets = self.generate_missing_datasets()
        _logger.info(f"All DATASETS from config:\n{target_datasets}")
        _logger.info(f"New DATASETS to CDF:\n{new_created_datasets}")

        # store all raw_dbs and datasets in scope of this configuration
        self.all_scope_ctx = {
            "raw": target_raw_dbs,  # all raw_dbs
            "datasets": target_datasets,  # all datasets
        }

        # reload deployed configs to be used as reference for group creation
        time.sleep(5)  # wait for datasets and raw_dbs to be created!
        self.load_deployed_config_from_cdf()

        # Special CDF Groups and their aad_mappings
        if with_special_groups == YesNoType.yes:
            self.generate_special_groups()

        # CDF Groups from configuration
        self.generate_groups()
        _logger.info("Created new CDF Groups")

        # and reload again now with latest group config too
        # dump all configs to yaml, as cope/paste template for delete_or_deprecate step
        self.dump_delete_template_to_yaml()
        _logger.info("Finished creating CDF Groups, Datasets and RAW Databases")

        # _logger.info(f'Bootstrap Pipelines: created: {len(created)}, deleted: {len(delete_ids)}')


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(prog_name="bootstrap_cli", version=__version__)
@click.option(
    "--cdf-project-name",
    help="Project to interact with transformations API, 'BOOTSTRAP_CDF_PROJECT',"
    "environment variable can be used instead. Required for OAuth2 and optional for api-keys.",
    envvar="BOOTSTRAP_CDF_PROJECT",
)
@click.option(
    "--cluster",
    default="westeurope-1",
    help="The CDF cluster where Transformations is hosted (e.g. greenfield, europe-west1-1),"
    "Provide this or make sure to set 'BOOTSTRAP_CDF_CLUSTER' environment variable.",
    envvar="BOOTSTRAP_CDF_CLUSTER",
)
@click.option(
    "--host",
    default="bluefield",
    help="The CDF cluster where Bootstrap-Pipelines are hosted (e.g. https://bluefield.cognitedata.com),"
    "Provide this or make sure to set 'BOOTSTRAP_CDF_HOST' environment variable.",
    envvar="BOOTSTRAP_CDF_HOST",
)
@click.option(
    "--api-key",
    help="API key to interact with transformations API. Provide this or make sure to set 'BOOTSTRAP_CDF_API_KEY',"
    "environment variable if you want to authenticate with API keys.",
    envvar="BOOTSTRAP_CDF_API_KEY",
)
@click.option(
    "--client-id",
    help="Client ID to interact with transformations API. Provide this or make sure to set,"
    "'BOOTSTRAP_IDP_CLIENT_ID' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_ID",
)
@click.option(
    "--client-secret",
    help="Client secret to interact with transformations API. Provide this or make sure to set,"
    "'BOOTSTRAP_IDP_CLIENT_SECRET' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_CLIENT_SECRET",
)
@click.option(
    "--token-url",
    help="Token URL to interact with transformations API. Provide this or make sure to set,"
    "'BOOTSTRAP_IDP_TOKEN_URL' environment variable if you want to authenticate with OAuth2.",
    envvar="BOOTSTRAP_IDP_TOKEN_URL",
)
@click.option(
    "--scopes",
    help="Scopes to interact with transformations API, relevant for OAuth2 authentication method,"
    "'BOOTSTRAP_IDP_SCOPES' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_SCOPES",
)
@click.option(
    "--audience",
    help="Audience to interact with transformations API, relevant for OAuth2 authentication method,"
    "'BOOTSTRAP_IDP_AUDIENCE' environment variable can be used instead.",
    envvar="BOOTSTRAP_IDP_AUDIENCE",
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
) -> None:
    context.obj = {
        "cluster": cluster,
        "host": host,
        "api_key": api_key,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_url": token_url,
        "scopes": scopes,
        "audience": audience,
        "cdf_project_name": cdf_project_name,
    }


@click.command(help="Deploy a set of bootstrap from a config-file")
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print debug information",
)
@click.option(
    "--with-special-groups",
    # having this as a flag is not working for gh-action 'actions.yml' manifest
    # instead using explicit choice options
    # is_flag=True,
    default="no",
    type=click.Choice(["yes", "no"], case_sensitive=False),
    help="Create special CDF Groups, which don't have capabilities (extractions, transformations)",
)
@click.pass_obj
def deploy(obj: Dict, config_file: str, debug: bool = False, with_special_groups: YesNoType = YesNoType.no) -> None:

    click.echo(click.style("Deploying CDF Project bootstrap...", fg="red"))

    # debug new yes/no flag
    click.echo(click.style(f"with_special_groups={with_special_groups} / {with_special_groups == YesNoType.yes}"))

    if debug:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        # load .env from file if exists
        load_dotenv()

        # _logger.debug(f'os.environ = {os.environ}')
        # print(f'os.environ= {os.environ}')

        # run deployment
        (
            BootstrapCore(config_file)
            # .validate_config() # TODO
            .deploy(with_special_groups=with_special_groups)
        )

        click.echo(click.style("CDF Project bootstrap deployed", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Prepare your CDF Project with a CDF Group 'cdf:bootstrap', which allows to run the 'deploy' command next,"
    "The 'prepare' command is only required once per CDF Project."
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print debug information",
)
@click.pass_obj
def prepare(obj: Dict, config_file: str, debug: bool = False) -> None:

    click.echo(click.style("Prepare CDF Project ...", fg="red"))

    if debug:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        # load .env from file if exists
        load_dotenv()

        # _logger.debug(f'os.environ = {os.environ}')
        # print(f'os.environ= {os.environ}')

        (
            BootstrapCore(config_file)
            # .validate_config() # TODO
            .prepare()
        )

        click.echo(click.style("CDF Project bootstrap prepared for running 'deploy' command next.", fg="blue"))

    except BootstrapConfigError as e:
        exit(e.message)


@click.command(
    help="Delete mode used to delete CDF Groups, Datasets and Raw Databases,"
    "CDF Groups and RAW Databases will be deleted, while Datasets will be archived and deprecated, not deleted"
)
@click.argument(
    "config_file",
    default="./config-bootstrap.yml",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print debug information",
)
@click.pass_obj
def delete(obj: Dict, config_file: str, debug: bool = False) -> None:

    click.echo(click.style("Delete CDF Project ...", fg="red"))

    if debug:
        # TODO not working yet :/
        _logger.setLevel("DEBUG")  # INFO/DEBUG

    try:
        # load .env from file if exists
        load_dotenv()

        # _logger.debug(f'os.environ = {os.environ}')
        # print(f'os.environ= {os.environ}')

        (
            BootstrapCore(config_file, delete=True)
            # .validate_config() # TODO
            .delete()
        )

        click.echo(
            click.style(
                "CDF Project relevant groups and raw_dbs are deleted and/or datasets are archived and deprecated ",
                fg="blue",
            )
        )

    except BootstrapConfigError as e:
        exit(e.message)


bootstrap_cli.add_command(deploy)
bootstrap_cli.add_command(prepare)
bootstrap_cli.add_command(delete)


def main() -> None:
    # call click.pass_context
    bootstrap_cli()


if __name__ == "__main__":
    main()
