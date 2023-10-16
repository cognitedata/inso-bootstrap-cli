from enum import ReprEnum  # new in 3.11
from typing import Any, Optional

from pydantic import Field

from .app_exceptions import BootstrapConfigError
from .common.base_model import Model

# because within f'' strings no backslash-character is allowed
NEWLINE = "\n"


class RoleType(str, ReprEnum):
    READ = "read"
    OWNER = "owner"
    ADMIN = "admin"  # aka root-account


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
    "robotics",
    "seismic",
    "sequences",
    "sessions",
    "templateGroups",
    "templateInstances",
    "threed",
    "timeSeries",
    "timeSeriesSubscriptions",
    "transformations",
    "types",
    "wells",
]

UndocumentedAclDefaultTypes = ["documentFeedback", "documentPipelines", "monitoringTasks", "notifications"]


def getAllAclTypes(with_undocumented_capabilities: bool = False):
    acl_types = AclDefaultTypes.copy()
    if with_undocumented_capabilities:
        acl_types.extend(UndocumentedAclDefaultTypes)
    return acl_types


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
        "timeSeriesSubscriptions",
        # undocumented alcls
        "documentFeedback",
        "documentPipelines",
        "monitoringTasks",
        "notifications",
    ]
)

# lookup of non-default actions per capability (acl) and role (owner/read/admin)
RoleTypeActions = {
    # owner datasets might only need READ and OWNER
    RoleType.OWNER: {  # else ["READ","WRITE"]
        "annotations": ["READ", "WRITE", "SUGGEST", "REVIEW"],
        "datasets": ["READ", "OWNER"],
        "groups": ["LIST"],
        "projects": ["LIST"],
        "raw": ["READ", "WRITE", "LIST"],
        "robotics": ["READ", "CREATE", "UPDATE", "DELETE"],
        "sessions": ["LIST", "CREATE"],
        "threed": ["READ", "CREATE", "UPDATE", "DELETE"],
        "documentFeedback": ["READ", "CREATE", "DELETE"],
    },
    RoleType.READ: {  # else ["READ"]
        "raw": ["READ", "LIST"],
        "groups": ["LIST"],
        "projects": ["LIST"],
        "sessions": ["LIST"],
    },
    # aka root-account
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
AclAdminTypes = list(RoleTypeActions[RoleType.ADMIN].keys())


# mixin 'str' to 'ReprEnum' to support comparison to string-values
# https://docs.python.org/3/library/enum.html#others
# https://stackoverflow.com/a/63028809/1104502
class YesNoType(str, ReprEnum):
    yes = "yes"
    no = "no"


class CommandMode(str, ReprEnum):
    PREPARE = "prepare"
    DEPLOY = "deploy"
    DELETE = "delete"
    DIAGRAM = "diagram"


class CacheUpdateMode(str, ReprEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ScopeCtxType(str, ReprEnum):
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
    create_only_mapped_cdf_groups: Optional[bool] = True
    mappings: list[IdpCdfMapping]


class SharedNode(Model):
    node_name: str


class SharedAccess(Model):
    owner: Optional[list[SharedNode]] = []
    read: Optional[list[SharedNode]] = []


class NamespaceNode(Model):
    node_name: str
    external_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    description: Optional[str] = ""
    shared_access: Optional[SharedAccess] = SharedAccess(owner=[], read=[])


class Namespace(Model):
    ns_name: str
    description: Optional[str]
    ns_nodes: list[NamespaceNode]


class BootstrapFeatures(Model):
    with_raw_capability: Optional[bool] = True
    with_datamodel_capability: Optional[bool] = True
    with_undocumented_capabilities: Optional[bool] = False
    group_prefix: Optional[str] = "cdf"
    aggregated_level_name: Optional[str] = "allprojects"
    dataset_suffix: Optional[str] = "dataset"
    space_suffix: Optional[str] = "space"
    rawdb_suffix: Optional[str] = "rawdb"
    rawdb_additional_variants: Optional[list[str]] = ["state"]


class BootstrapCoreConfig(Model):
    """
    Configuration parameters for CDF Project Bootstrap,
    deploy(create), prepare, diagram mode
    """

    # providing a default for optional 'features' set not avaialble
    # 1:1 default values as used in 'BootstrapFeatures'
    # TODO: remove Field() wrapper?
    features: Optional[BootstrapFeatures] = Field(
        default=BootstrapFeatures(
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

    # [] works too > https://stackoverflow.com/a/63808835/1104502
    namespaces: list[Namespace] = []  # Field(default_factory=list)

    idp_cdf_mappings: Optional[list[IdpCdfMappingProjects]] = []

    def create_only_mapped_cdf_groups(self, cdf_project) -> bool:
        assert self.idp_cdf_mappings is not None
        idp_cdf_mapping_project = [
            idp_cdf_mapping_project
            for idp_cdf_mapping_project in self.idp_cdf_mappings
            if cdf_project == idp_cdf_mapping_project.cdf_project
        ]
        if len(idp_cdf_mapping_project) > 1:
            raise BootstrapConfigError(f"Found more than one project for cdf_project {cdf_project}")

        # TODO: getting tired of adding `assert is not none` checks before
        #   because pylance not values the **default** values for `Optional[..]` types
        return idp_cdf_mapping_project[0].create_only_mapped_cdf_groups

    def get_idp_cdf_mapping_for_group(self, cdf_project, cdf_group) -> IdpCdfMapping:
        """
        Return the IdpCdfMapping for the given cdf_project and cdf_group (two nested-loops with filter)
        """
        assert self.idp_cdf_mappings
        mappings = [
            mapping
            for idp_cdf_mapping_project in self.idp_cdf_mappings
            if cdf_project == idp_cdf_mapping_project.cdf_project
            for mapping in idp_cdf_mapping_project.mappings
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

    datasets: Optional[list] = []
    groups: Optional[list] = []
    raw_dbs: Optional[list] = []
    spaces: Optional[list] = []
