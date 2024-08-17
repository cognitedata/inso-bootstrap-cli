from typing import Optional
import networkx as nx
import itertools

from cognite.client.data_classes import capabilities

from pydantic import model_validator
from .common.base_model import Model
from rich import print as rprint

"""
groups
    capabilities
        acls
        scopes
        actions

1. acl-set is
    a) a composition of acl-sets
    b) exclude of acl-sets
    b) a list of explicit acls (e.g. "assetsAcl")
2. scope-set is
    a) a composition of scope-sets
    b) exclude of scope-sets
    c) a list of explicit scopes (e.g. "src:all:db")
        - a scoe is either a rawdb, space or dataset
3. action-set is
    a) a list of action-mappings to resolve actions for a given acl
        - an action-mapping is a dict of acl to list of actions
    b) action-sets don't suport compose or exclude
4. capability-set is
    a) a composition of capability-sets
    b) exclude of capability-sets
    c) a list of capabilities
        - a capability is a list of triples (acls, scopes, actions)
"""


class Rawdb(Model):
    name: str


class Space(Model):
    name: str


class Dataset(Model):
    name: str


class ActionSet(Model):
    name: str
    description: str
    action_mapping: dict[str, list[str]] = {}


class AclSet(Model):
    name: str
    description: str = ""
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    explicit: Optional[list[str]] = []


class ExplicitScopes(Model):
    rawdbs: Optional[list[Rawdb]] = []
    spaces: Optional[list[Space]] = []
    datasets: Optional[list[Dataset]] = []


class ScopeSet(Model):
    name: str
    description: str = ""
    all_scope: Optional[bool] = False
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    explicit: Optional[ExplicitScopes] = []


class Capability(Model):
    acls: list[str]
    scopes: list[str]
    actions: list[str]


class CapabilitySet(Model):
    name: str
    description: str
    compose: Optional[list[str]] = []
    exclude: Optional[list[str]] = []
    capabilities: list[Capability] = []


class Group(Model):
    name: str
    capability_sets: list[str]
    metadata: Optional[dict[str, str]] = {}
    sourceId: str


class Project(Model):
    name: str
    groups: list[Group]


class Config(Model):
    projects: list[Project]
    action_sets: list[ActionSet]
    acl_sets: list[AclSet]
    scope_sets: list[ScopeSet]
    capability_sets: list[CapabilitySet]

    @model_validator(mode="after")
    def validate_name_references(self, info):
        """validate loaded config
        1. get all declared names and cdf-capabilities
        2. action-set mappings from acl to actions are valid
        3. scope-set self-references are valid
        4. acl-set self-references are valid
        5. capability-set self-references valid
        6. capability-set references to acls, scopes and actions are valid
        7. capability-set references in groups are valid
        """

        print("==> Validating Name References <==")

        # 1. get declared names
        cdf_acls = capabilities._CAPABILITY_CLASS_BY_NAME.keys()
        cdf_acl_actions = {
            acl_name: [a.value for a in acl.Action.__members__.values()]
            for acl_name, acl in capabilities._CAPABILITY_CLASS_BY_NAME.items()
        }
        # {'analyticsAcl': ['READ', 'EXECUTE', 'LIST'],
        #  'annotationsAcl': ['READ', 'WRITE', 'SUGGEST', 'REVIEW'],
        #  'assetsAcl': ['READ', 'WRITE'],
        scope_set_names = [s.name for s in self.scope_sets]
        acl_set_names = [s.name for s in self.acl_sets]
        acl_set_supported_names = set(acl_set_names) | set(itertools.chain(*[s.explicit for s in self.acl_sets]))
        action_set_names = [s.name for s in self.action_sets]
        capability_set_names = [s.name for s in self.capability_sets]

        rprint(
            f"scope_set_names: {sorted(scope_set_names)}\n"
            f"acl_set_names: {sorted(acl_set_names)}\n"
            f"acl_set_supported_names: {sorted(acl_set_supported_names)}\n"
            f"action_set_names: {sorted(action_set_names)}\n"
            f"capability_set_names: {sorted(capability_set_names)}\n"
        )

        for action_set in self.action_sets:
            for acl_name, actions in action_set.action_mapping.items():
                if acl_name == "_":  # skip the default acl
                    continue
                for action in actions:
                    if action not in cdf_acl_actions[acl_name]:
                        raise ValueError(
                            f"Invalid Action name: '{action}' used in action set: '{action_set.name}' for acl: '{acl_name}'"
                        )

        # 2. acl-set self-references are valid
        for acl_set in self.acl_sets:
            if acl_set.compose:
                for compose_name in acl_set.compose:
                    if compose_name not in acl_set_supported_names:
                        raise ValueError(f"Invalid acl compose name: '{compose_name}' used in acl: '{acl_set.name}'")
            if acl_set.exclude:
                for exclude_name in acl_set.exclude:
                    if exclude_name not in acl_set_supported_names:
                        raise ValueError(f"Invalid acl exclude name: '{exclude_name}' used in acl: '{acl_set.name}'")
            if acl_set.explicit:
                for explicit_name in acl_set.explicit:
                    if explicit_name not in cdf_acls:
                        raise ValueError(f"Invalid acl explicit name: '{explicit_name}' used in acl: '{acl_set.name}'")

        # 3. scope-set self-references are valid
        for scope_set in self.scope_sets:
            if scope_set.compose:
                for compose_name in scope_set.compose:
                    if compose_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid SetScope compose name: '{compose_name}' used in scope: '{scope_set.name}'"
                        )
            if scope_set.exclude:
                for exclude_name in scope_set.exclude:
                    if exclude_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid SetScope exclude name: '{exclude_name}' used in scope: '{scope_set.name}'"
                        )

        # 4. capability-set self-references valid
        for capability_set in self.capability_sets:
            if capability_set.compose:
                for compose_name in capability_set.compose:
                    if compose_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid SetScope compose name: '{compose_name}' used in capabilty: '{capability_set.name}'"
                        )
            if capability_set.exclude:
                for exclude_name in capability_set.exclude:
                    if exclude_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid SetScope exclude name: '{exclude_name}' used in capabilty: '{capability_set.name}'"
                        )

        # 5. capability-set references to acls, scopes and actions are valid
        for capability_set in self.capability_sets:
            for capability in capability_set.capabilities:
                for acl_name in capability.acls:
                    if acl_name not in acl_set_supported_names:
                        raise ValueError(f"Invalid ACL name: '{acl_name}' used in capabilty: '{capability_set.name}'")
                for scope_name in capability.scopes:
                    if scope_name not in scope_set_names:
                        raise ValueError(
                            f"Invalid Scope name: '{scope_name}' used in capabilty: '{capability_set.name}'"
                        )
                for action_name in capability.actions:
                    if action_name not in action_set_names:
                        raise ValueError(
                            f"Invalid Action name: '{action_name}' used in capabilty: '{capability_set.name}'"
                        )

        # 6. capability-set references in groups are valid
        for idp_cdf_mapping in self.projects:
            for group in idp_cdf_mapping.groups:
                for capability_set_name in group.capability_sets:
                    if capability_set_name not in capability_set_names:
                        raise ValueError(
                            f"Invalid CapabilitySet name: '{capability_set_name}' used in group: '{group.name}'"
                        )

        return self

    @model_validator(mode="after")
    def validate_dag(self):

        print("==> Validating DAG <==")

        graph = nx.DiGraph()

        node_acl = lambda x: f"acl|{x}"
        node_scope = lambda x: f"scope|{x}"
        node_action = lambda x: f"action|{x}"
        node_capability = lambda x: f"capability|{x}"
        node_group = lambda x: f"group|{x}"
        node_project = lambda x: f"project|{x}"
        node_scope_ds = lambda x: f"scope-ds|{x}"
        node_scope_spc = lambda x: f"scope-spc|{x}"
        node_scope_rawdb = lambda x: f"scope-db|{x}"

        for project in self.projects:
            graph.add_node(node_project(project.name))
            for group in project.groups:
                graph.add_edge(node_project(project.name), node_group(group.name))
                for capability_set_name in group.capability_sets:
                    graph.add_edge(node_group(group.name), node_capability(capability_set_name))

        # Add nodes and edges for capability-sets
        for capability_set in self.capability_sets:
            graph.add_node(node_capability(capability_set.name))
            if capability_set.compose:
                for compose_name in capability_set.compose:
                    graph.add_edge(node_capability(capability_set.name), node_capability(compose_name))
            if capability_set.exclude:
                for exclude_name in capability_set.exclude:
                    graph.add_edge(node_capability(capability_set.name), node_capability(exclude_name))
            if capability_set.capabilities:
                for capability in capability_set.capabilities:
                    for acl_name in capability.acls:
                        graph.add_edge(node_capability(capability_set.name), node_acl(acl_name))
                    for scope_name in capability.scopes:
                        graph.add_edge(node_capability(capability_set.name), node_scope(scope_name))
                    for action_name in capability.actions:
                        graph.add_edge(node_capability(capability_set.name), node_action(action_name))

        # Add nodes and edges for acl-sets
        for acl_set in self.acl_sets:
            graph.add_node(node_acl(acl_set.name))
            if acl_set.compose:
                for compose_name in acl_set.compose:
                    graph.add_edge(node_acl(acl_set.name), node_acl(compose_name))
            if acl_set.exclude:
                for exclude_name in acl_set.exclude:
                    graph.add_edge(node_acl(acl_set.name), node_acl(exclude_name))

        # # Add nodes and edges for scope-sets
        for scope_set in self.scope_sets:
            graph.add_node(node_scope(scope_set.name))
            if scope_set.compose:
                for compose_name in scope_set.compose:
                    graph.add_edge(node_scope(scope_set.name), node_scope(compose_name))
            if scope_set.exclude:
                for exclude_name in scope_set.exclude:
                    graph.add_edge(node_scope(scope_set.name), node_scope(exclude_name))
            if scope_set.explicit:
                for rawdb in scope_set.explicit.rawdbs:
                    graph.add_edge(node_scope(scope_set.name), node_scope_rawdb(rawdb.name))
                for space in scope_set.explicit.spaces:
                    graph.add_edge(node_scope(scope_set.name), node_scope_spc(space.name))
                for dataset in scope_set.explicit.datasets:
                    graph.add_edge(node_scope(scope_set.name), node_scope_ds(dataset.name))

        rprint(graph)

        # Function to print the graph as an indented list
        def print_graph(node, indent=0):
            print(" " * indent + node)
            for child in graph.successors(node):
                print_graph(child, indent + 4)

        # # Print the graph starting from nodes with no incoming edges
        for node in graph.nodes:
            if graph.in_degree(node) == 0:
                print_graph(node)

        # Check if the graph is a DAG
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Configuration contains cycles")

        return self


# Example usage:
if __name__ == "__main__":
    from pathlib import Path
    import yaml

    # Get the path of the current script
    current_script_path = Path(__file__).resolve().parent

    #
    yaml_file = current_script_path / "config/240816-v4-tk-config-sketch.yml"
    config_data = yaml.safe_load(yaml_file.read_text())
    config = Config(**config_data)

    # print("==> Parsed and validated config <==")

    # rprint(capabilities._CAPABILITY_CLASS_BY_NAME.keys())
