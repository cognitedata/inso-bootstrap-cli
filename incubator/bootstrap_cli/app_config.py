from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .app_exceptions import BootstrapConfigError


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


class RoleType(str, Enum):
    READ = "read"
    OWNER = "owner"
    ADMIN = "admin"


#
# pydantic class definitions
#
def to_kebap_case(value: str) -> str:
    """Creates alias names from Python compatible snake_case '_' to yaml typical kebap-style ('-')
    # https://www.freecodecamp.org/news/snake-case-vs-camel-case-vs-pascal-case-vs-kebab-case-whats-the-difference/

    Args:
        value (str): the value to generate an alias for

    Returns:
        str: alias in kebap-style
    """
    return value.replace("_", "-")


class KebapBaseModel(BaseModel):
    """Subclass with alias_generator
    Using BaseModel instead of BaseSettings as latter throws FutureWarnings
    when using 'Field(alias=..)' or 'alias_generator'
    """

    class Config:
        # generate for each field an alias in kebap-case (hyphen)
        alias_generator = to_kebap_case
        # an aliased field may be populated by its name as given by the model attribute, as well as the alias
        # this supports both cases to be mixed!
        allow_population_by_field_name = True


class CogniteIdpConfig(KebapBaseModel):
    # fields required for OIDC client-credentials authentication
    client_name: Optional[str]
    client_id: str
    secret: str
    scopes: List[str]
    token_url: Optional[str]


class CogniteConfig(KebapBaseModel):
    host: str
    project: str
    idp_authentication: CogniteIdpConfig

    # compatibility properties to keep get_cognite_client() in sync with other solutions
    # which are using flat-fields, no nesting and a bit different names
    @property
    def base_url(self) -> List[str]:
        return self.host

    @property
    def token_url(self) -> str:
        return self.idp_authentication.token_url

    @property
    def scopes(self) -> List[str]:
        return self.idp_authentication.scopes

    @property
    def client_name(self) -> List[str]:
        return self.idp_authentication.client_name

    @property
    def client_id(self) -> List[str]:
        return self.idp_authentication.client_id

    @property
    def client_secret(self) -> List[str]:
        return self.idp_authentication.secret


class IdpCdfMapping(KebapBaseModel):
    cdf_group: str
    idp_source_id: Optional[str]
    idp_source_name: Optional[str]


class IdpCdfMappingProjects(KebapBaseModel):
    cdf_project: str
    mappings: List[IdpCdfMapping]


class SharedNode(KebapBaseModel):
    node_name: str


class SharedAccess(KebapBaseModel):
    owner: Optional[List[SharedNode]] = Field(default_factory=list)
    read: Optional[List[SharedNode]] = Field(default_factory=list)


class NamespaceNode(KebapBaseModel):
    node_name: str
    external_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    description: Optional[str] = ""
    shared_access: Optional[SharedAccess] = SharedAccess(owner=[], read=[])


class Namespace(KebapBaseModel):
    ns_name: str
    description: Optional[str]
    ns_nodes: List[NamespaceNode]


class BootstrapFeatures(KebapBaseModel):
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


class BootstrapCoreConfig(KebapBaseModel):
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


class BootstrapDeleteConfig(KebapBaseModel):
    """
    Configuration parameters for CDF Project Bootstrap 'delete' command
    """

    datasets: Optional[List] = []
    groups: Optional[List] = []
    raw_dbs: Optional[List] = []
    spaces: Optional[List] = []
