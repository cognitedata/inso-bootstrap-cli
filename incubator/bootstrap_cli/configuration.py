from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from cognite.extractorutils.configtools import CogniteConfig, LoggingConfig, load_yaml
from dotenv import load_dotenv


# mixin 'str' to 'Enum' to support comparison to string-values
# https://docs.python.org/3/library/enum.html#others
# https://stackoverflow.com/a/63028809/1104502
class YesNoType(str, Enum):
    yes = "yes"
    no = "no"


@dataclass
class IdpCdfMapping:
    cdf_group: str
    idp_source_id: str
    idp_source_name: Optional[str]


@dataclass
class IdpCdfMappingProjects:
    cdf_project: str
    mappings: List[IdpCdfMapping]


@dataclass
class SharedNode:
    node_name: str


@dataclass
class SharedAccess:
    owner: Optional[List[SharedNode]]
    read: Optional[List[SharedNode]]

    def __post_init__(self):
        """Handle default optional field settings"""
        # check each property for None and set default value
        if self.owner is None:
            self.owner = []
        if self.read is None:
            self.read = []


@dataclass
class NamespaceNode:
    node_name: str
    description: Optional[str]
    external_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    shared_access: Optional[SharedAccess]

    def __post_init__(self):
        """Handle default optional field settings"""
        # check each property for None and set default value
        if self.description is None:
            self.description = ""
        if self.shared_access is None:
            self.shared_access = SharedAccess([], [])


@dataclass
class Namespace:
    ns_name: str
    description: Optional[str]
    ns_nodes: List[NamespaceNode]


@dataclass
class BootstrapFeatures:
    # load_yaml includes mapping from several string like 'yes|no' to boolean
    with_special_groups: Optional[bool]
    with_raw_capability: Optional[bool]
    group_prefix: Optional[str]
    aggregated_level_name: Optional[str]
    dataset_suffix: Optional[str]
    rawdb_suffix: Optional[str]
    rawdb_additional_variants: Optional[List[str]]

    def __post_init__(self):
        """Handle default optional field settings"""

        # check each property for None and set default value
        if self.with_special_groups is None:
            self.with_special_groups = False
        if self.with_raw_capability is None:
            self.with_raw_capability = False
        if self.group_prefix is None:
            self.group_prefix = "cdf"
        if self.aggregated_level_name is None:
            self.aggregated_level_name = "allprojects"
        if self.dataset_suffix is None:
            self.dataset_suffix = "dataset"
        if self.rawdb_suffix is None:
            self.rawdb_suffix = "rawdb"
        if self.rawdb_additional_variants is None:
            self.rawdb_additional_variants = ["state"]

        print(f"BootstrapFeatures2 {self=}")


@dataclass
class BootstrapCoreConfig:
    """
    Configuration parameters for CDF Project Bootstrap, deploy(create) & prepare mode
    """

    features: Optional[BootstrapFeatures]
    idp_cdf_mappings: Optional[List[IdpCdfMappingProjects]]
    namespaces: List[Namespace]

    def get_idp_cdf_mapping_for_group(self, cdf_project, cdf_group) -> IdpCdfMapping:
        """
        Return the IdpCdfMapping for the given cdf_project and cdf_group
        """
        mappings = [
            mapping
            for idp_cdf_mapping_projects in self.idp_cdf_mappings
            if cdf_project == idp_cdf_mapping_projects.cdf_project
            for mapping in idp_cdf_mapping_projects.mappings
            if cdf_group == mapping.cdf_group
        ]
        assert len(mappings) <= 1, f"More than one mapping for cdf_group {cdf_group} in cdf_project {cdf_project}"
        return mappings[0] if mappings else IdpCdfMapping(cdf_group, None, None)

    def __post_init__(self):
        """Handle default optional field settings"""
        self.idp_cdf_mappings = self.idp_cdf_mappings or []
        # check if features are available, else load yaml with default values
        self.features = self.features or load_yaml(
            config_type=BootstrapFeatures,
            # feature default values
            source="""
            # available as cli paramaters only atm
            with-special-groups: no
            with-raw-capability: yes
            # default hard-coded names atm, which might be required to change
            group-prefix: cdf
            aggregated-level-name: allprojects
            dataset-suffix: dataset
            # not sure about providing multiple datasets per ns-node, atm it is only one
            rawdb-suffix: rawdb
            rawdb-additional-variants:
            # provide more than one rawdb per ns-nodes
            # atm hardcoded is one additional rawdb
            - state
            """,
        )


@dataclass
class BootstrapBaseConfig:

    logger: LoggingConfig
    cognite: CogniteConfig
    # logger: Optional[Dict[str, Any]]
    # cognite: Optional[Dict[str, Any]]
    # optional for OIDC authentication
    token_custom_args: Optional[Dict[str, Any]]

    @classmethod
    def from_yaml(cls, filepath):
        try:
            with open(filepath) as file:
                return load_yaml(source=file, config_type=cls)
        except FileNotFoundError as exc:
            print("Incorrect file path, error message: ", exc)
            raise

    def __post_init__(self):
        """Handle default optional field settings"""
        self.token_custom_args = self.token_custom_args or {}


@dataclass
class BootstrapDeployConfig(BootstrapBaseConfig):
    """
    Configuration parameters for CDF Project Bootstrap:
    - 'prepare'
    - 'deploy'
    - 'diagram'
    commands
    """

    bootstrap: BootstrapCoreConfig


@dataclass
class BootstrapDeleteConfig(BootstrapBaseConfig):
    """
    Configuration parameters for CDF Project Bootstrap 'delete' command
    """

    delete_or_deprecate: Dict[str, Any] = field(default_factory=dict)


if __name__ == "__main__":
    load_dotenv()
    config = BootstrapDeployConfig.from_yaml("configs/config-simple-v2-draft.yml")
    print(config.bootstrap.namespaces)
