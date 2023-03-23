from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from .app_exceptions import BootstrapConfigError
from .common.base_model import Model

# because within f'' strings no backslash-character is allowed
NEWLINE = "\n"


class RoleType(str, Enum):
    READ = "read"
    OWNER = "owner"
    ADMIN = "admin"


#
# GENERIC configurations
# extend when new capability (acl) is available
# check if action_dimensions must be extended with non-default capabilities:
#   which are owner: ["READ","WRITE"]
#   and read: ["READ"])
#
AclDefaultTypes = [
    "assets",
    "annotations",
    "dataModels",
    "dataModelInstances",
    "datasets",
    "digitalTwin",
    "entitymatching",
    "events",
    "extractionConfigs",
    "extractionPipelines",
    "extractionRuns",
    "files",
    "functions",
    "geospatial",
    "geospatialCrs",
    "groups",
    "labels",
    "projects",
    "raw",
    "relationships",
    "seismic",
    "sequences",
    "sessions",
    "templateGroups",
    "templateInstances",
    "threed",
    "timeSeries",
    "transformations",
    "types",
    "wells",
]

# capabilities (acl) which only support  scope: {"all":{}}
# a subset of AclDefaultTypes
AclAllScopeOnlyTypes = set(
    [
        "projects",
        "sessions",
        "annotations",
        "entitymatching",
        "functions",
        "types",
        "threed",
        "seismic",
        "digitalTwin",
        "geospatial",
        "geospatialCrs",
        "wells",
    ]
)

# lookup of non-default actions per capability (acl) and role (owner/read/admin)
ActionDimensions = {
    # owner datasets might only need READ and OWNER
    RoleType.OWNER: {  # else ["READ","WRITE"]
        "raw": ["READ", "WRITE", "LIST"],
        "datasets": ["READ", "OWNER"],
        "groups": ["LIST"],
        # TODO: requires configuration and support of idscope
        # "securityCategories": ["MEMBEROF", "LIST"],
        "projects": ["LIST"],
        "robotics": ["READ", "CREATE", "UPDATE", "DELETE"],
        "sessions": ["LIST", "CREATE"],
        "threed": ["READ", "CREATE", "UPDATE", "DELETE"],
    },
    RoleType.READ: {  # else ["READ"]
        "raw": ["READ", "LIST"],
        "groups": ["LIST"],
        # TODO: requires configuration and support of idscope
        # "securityCategories": ["MEMBEROF", "LIST"],
        "projects": ["LIST"],
        "sessions": ["LIST"],
    },
    RoleType.ADMIN: {
        "datasets": ["READ", "WRITE", "OWNER"],
        "groups": ["LIST", "READ", "CREATE", "UPDATE", "DELETE"],
        # TODO: can "space" scope creation be limted to root-account
        # "dataModels": ["READ", "WRITE"],
        "securityCategories": ["MEMBEROF", "LIST", "CREATE", "DELETE"],
        "projects": ["READ", "UPDATE", "LIST"],
    },
}

# give precedence when merging over acl_default_types
AclAdminTypes = list(ActionDimensions[RoleType.ADMIN].keys())


# mixin 'str' to 'Enum' to support comparison to string-values
# https://docs.python.org/3/library/enum.html#others
# https://stackoverflow.com/a/63028809/1104502
class YesNoType(str, Enum):
    yes = "yes"
    no = "no"


class CommandMode(str, Enum):
    PREPARE = "prepare"
    DEPLOY = "deploy"
    DELETE = "delete"
    DIAGRAM = "diagram"


class CacheUpdateMode(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ScopeCtxType(str, Enum):
    DATASET = "datasets"
    SPACE = "spaces"
    RAWDB = "raw_dbs"
    GROUP = "groups"


class IdpCdfMapping(Model):
    cdf_group: str
    idp_source_id: Optional[str]
    idp_source_name: Optional[str]


class IdpCdfMappingProjects(Model):
    cdf_project: str
    mappings: List[IdpCdfMapping]


class SharedNode(Model):
    node_name: str


class SharedAccess(Model):
    owner: Optional[List[SharedNode]] = Field(default_factory=list)
    read: Optional[List[SharedNode]] = Field(default_factory=list)


class NamespaceNode(Model):
    node_name: str
    external_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    description: Optional[str] = ""
    shared_access: Optional[SharedAccess] = SharedAccess(owner=[], read=[])


class Namespace(Model):
    ns_name: str
    description: Optional[str]
    ns_nodes: List[NamespaceNode]


class BootstrapFeatures(Model):
    with_special_groups: Optional[bool] = False
    with_raw_capability: Optional[bool] = True
    # TODO: datamodel / spaces / fdm?
    with_datamodel_capability: Optional[bool] = False
    group_prefix: Optional[str] = "cdf"
    aggregated_level_name: Optional[str] = "allprojects"
    dataset_suffix: Optional[str] = "dataset"
    space_suffix: Optional[str] = "space"
    rawdb_suffix: Optional[str] = "rawdb"
    rawdb_additional_variants: Optional[List[str]] = ["state"]


class BootstrapCoreConfig(Model):
    """
    Configuration parameters for CDF Project Bootstrap,
    deploy(create), prepare, diagram mode
    """

    # providing a default for optional 'features' set not avaialble
    # 1:1 default values as used in 'BootstrapFeatures'
    features: Optional[BootstrapFeatures] = Field(
        default=BootstrapFeatures(
            **dict(
                with_special_groups=False,
                with_raw_capability=True,
                with_datamodel_capability=False,
                group_prefix="cdf",
                aggregated_level_name="allprojects",
                dataset_suffix="dataset",
                space_suffix="space",
                rawdb_suffix="rawdb",
                rawdb_additional_variants=["state"],
            )
        )
    )

    # [] works too > https://stackoverflow.com/a/63808835/1104502
    namespaces: List[Namespace] = Field(default_factory=list)
    # alias_generator
    idp_cdf_mappings: Optional[List[IdpCdfMappingProjects]] = Field(default_factory=list)

    def get_idp_cdf_mapping_for_group(self, cdf_project, cdf_group) -> IdpCdfMapping:
        """
        Return the IdpCdfMapping for the given cdf_project and cdf_group (two nested-loops with filter)
        """
        mappings = [
            mapping
            for idp_cdf_mapping_projects in self.idp_cdf_mappings
            if cdf_project == idp_cdf_mapping_projects.cdf_project
            for mapping in idp_cdf_mapping_projects.mappings
            if cdf_group == mapping.cdf_group
        ]
        if len(mappings) > 1:
            raise BootstrapConfigError(
                f"Found more than one mapping for cdf_group {cdf_group} in cdf_project {cdf_project}"
            )

        return mappings[0] if mappings else IdpCdfMapping(cdf_group=cdf_group, idp_source_id=None, idp_source_name=None)


class BootstrapDeleteConfig(Model):
    """
    Configuration parameters for CDF Project Bootstrap 'delete' command
    """

    datasets: Optional[List] = []
    groups: Optional[List] = []
    raw_dbs: Optional[List] = []
    spaces: Optional[List] = []
