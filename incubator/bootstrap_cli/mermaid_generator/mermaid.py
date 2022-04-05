# std-lib
import logging
from datetime import datetime
from dataclasses import dataclass

# type-hints
from enum import Enum
from typing import Dict, List, Tuple, TypeVar, Type, Union

_logger = logging.getLogger(__name__)


# helper function
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#
# Mermaid Dataclasses
#
# Subgraph can contain Subgraph, Nodes and Edges
# Edge only reference source/dest Nodes by their (full) name
#
#
# because within f'' strings no backslash-character is allowed
NEWLINE = "\n"


@dataclass
class MermaidFlowchartElement:
    name: str
    # TODO: ading default_factory value, will break the code
    # see https://stackoverflow.com/q/51575931/1104502
    comments: List[str]

    # dump comments
    def comments_to_mermaid(self):
        return f"""{NEWLINE.join([f'%% {comment}' for comment in self.comments]) + NEWLINE}""" if self.comments else ""


# https://mermaid-js.github.io/mermaid/#/flowchart?id=node-shapestyle-and-arrowstyle
@dataclass
class Node(MermaidFlowchartElement):
    short: str

    def __repr__(self):
        # TODO: how to add comments from super class the right way?
        return self.comments_to_mermaid() + f"""{self.name}""" + (rf"""["{self.short}"]""" if self.short else "")


@dataclass
class RoundedNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}""" + (rf"""("{self.short}")""" if self.short else "")


@dataclass
class TrapezNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}""" + (rf"""[\"{self.short}"/]""" if self.short else "")


@dataclass
class AssymetricNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}""" + (rf""">"{self.short}"]""" if self.short else "")


@dataclass
class SubroutineNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}""" + (rf"""[["{self.short}"]]""" if self.short else "")


@dataclass
class Edge(MermaidFlowchartElement):
    # from / to cannot be used as "from" is a reserved keyword
    dest: str
    annotation: str

    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}-->{self.dest}"""
        # cannot render a 🕑 on an edge annotation
        # return (
        #     rf'''{self.name}-->|{self.annotation}|{self.dest}'''
        #     if self.annotation
        #     else f'''{self.name}-->{self.dest}'''
        #     )


@dataclass
class DottedEdge(Edge):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.name}-.->{self.dest}"""


# type-hint for ExtpipesCore instance response
T_Subgraph = TypeVar("T_Subgraph", bound="Subgraph")


@dataclass
class Subgraph(MermaidFlowchartElement):
    elements: List[Union[T_Subgraph, Node]]

    def __contains__(self, name):
        return name in [elem.name for elem in self.elements]

    def __getitem__(self, name):
        if name in self.elements:
            return [elem.name for elem in self.elements if elem.name == name][0]  # exactly one expected

    def __repr__(self):
        return (
            self.comments_to_mermaid()
            + f"""
subgraph "{self.name}"
{NEWLINE.join([f'  {elem}' for elem in self.elements])}
end
"""
        )


class GraphRegistry:
    """
    A graph reqistry is
    * a list of elements and edges to render (representing the "graph")
    * provides a registry for lookup of already created subgraphs by name for reuse ("get_or_create")
    * supports printing the graph in a mermaid-compatible format
    """

    def __init__(self, elements=[]):
        self.subgraph_registry: Dict[str, Type[Subgraph]] = {}
        # nested
        self.elements: List[Union[T_Subgraph, Node, Edge]] = elements
        # final block of edges
        self.edges: List[Edge] = []

    def get_or_create(self, subgraph_name):
        return self.subgraph_registry.setdefault(
            # get if exists
            subgraph_name,
            # create if new
            Subgraph(name=subgraph_name, elements=[], comments=[]),
        )

    #     def __str__(self):
    #         for elem in self.elements:
    #             print(elem.name)

    def to_mermaid(self, to_markdown=False) -> str:
        markdownPrefix = "```mermaid\n" if to_markdown else ""
        markdownSuffix = "\n```\n" if to_markdown else ""

        mermaid_flowchart = (
            markdownPrefix
            + "\n".join(
                (
                    ["graph LR", f"%% {timestamp()} - Script generated Mermaid diagram"]
                    + list(map(str, self.elements + self.edges))
                )
            )
            + markdownSuffix
        )

        _logger.info(f"Generated {len(mermaid_flowchart)} characters")

        return mermaid_flowchart


def diagram(config, to_markdown=True):
    # load deployed groups, datasets, raw_dbs with their ids and metadata
    config.load_deployed_config_from_cdf()

    def get_group_name_and_scopes(
        action: str = None, group_ns: str = None, group_core: str = None, root_account: str = None
    ) -> Tuple[str, List[str]]:

        group_name_full_qualified, scope_ctx_by_action = None, None

        # detail level like cdf:src:001:public:read
        if action and group_ns and group_core:
            group_name_full_qualified = f"{config.GROUP_NAME_PREFIX}{group_core}:{action}"
            scope_ctx_by_action = config.get_scope_ctx_groupedby_action(action, group_ns, group_core)
        # group-type level like cdf:src:all:read
        elif action and group_ns:
            # 'all' groups on group-type level
            # (access to all datasets/ raw-dbs which belong to this group-type)
            group_name_full_qualified = f"{config.GROUP_NAME_PREFIX}{group_ns}:{config.AGGREGATED_GROUP_NAME}:{action}"
            scope_ctx_by_action = config.get_scope_ctx_groupedby_action(action, group_ns)
        # top level like cdf:all:read
        elif action:
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            group_name_full_qualified = f"{config.GROUP_NAME_PREFIX}{config.AGGREGATED_GROUP_NAME}:{action}"
            # scope_ctx_by_action =  self.get_scope_ctx_groupedby_action(
            #     action, self.all_scope_ctx
            # )
        # root level like cdf:root
        elif root_account:  # no parameters
            # all (no limits)
            group_name_full_qualified = f"{config.GROUP_NAME_PREFIX}{root_account}"

        return group_name_full_qualified, scope_ctx_by_action

    class SubgraphTypes(str, Enum):
        aad = "AAD Groups"
        owner = "'Owner' Groups"
        read = "'Read' Groups"
        # OWNER
        core_cdf_owner = "Core Level (Owner)"
        ns_cdf_owner = "Namespace Level (Owner)"
        scope_owner = "Scopes (Owner)"
        # READ
        core_cdf_read = "Core Level (Read)"
        ns_cdf_read = "Namespace Level (Read)"
        scope_read = "Scopes (Read)"

    def temp_group(
        graph: GraphRegistry, action: str = None, group_ns: str = None, group_core: str = None, root_account: str = None
    ) -> None:

        if root_account:
            return

        group_name, scope_ctx_by_action = get_group_name_and_scopes(action, group_ns, group_core, root_account)
        aad_source_id, aad_source_name = config.aad_mapping_lookup.get(group_name, [None, None])

        _logger.info(f"{group_name=} : {scope_ctx_by_action=} [{aad_source_name=}]")

        # preload master subgraphs
        core_cdf = graph.get_or_create(getattr(SubgraphTypes, f"core_cdf_{action}"))
        ns_cdf_graph = graph.get_or_create(getattr(SubgraphTypes, f"ns_cdf_{action}"))
        scope_graph = graph.get_or_create(getattr(SubgraphTypes, f"scope_{action}"))

        aad = graph.get_or_create(SubgraphTypes.aad)
        if aad_source_name and (aad_source_name not in aad):
            aad.elements.append(TrapezNode(name=aad_source_name, short=aad_source_name, comments=[aad_source_id]))
            # link from table to transformation
            graph.edges.append(Edge(name=aad_source_name, dest=group_name, annotation=None, comments=[]))

        # {'owner': {'raw': ['src:002:weather:rawdb', 'src:002:weather:rawdb:state'],
        #       'datasets': ['src:002:weather:dataset']},
        # 'read': {'raw': [], 'datasets': []}}

        # core-level like cdf:src:001:public:read
        if action and group_ns and group_core:
            core_cdf.elements.append(RoundedNode(name=group_name, short=group_name, comments=""))

            # link from 'src:all' to 'src:001:sap'
            edge_type_cls = Edge if action == "owner" else DottedEdge
            graph.edges.append(
                edge_type_cls(
                    # link from all:{ns}
                    name=f"{config.GROUP_NAME_PREFIX}{group_ns}:{config.AGGREGATED_GROUP_NAME}:{action}",
                    dest=group_name,
                    annotation="",
                    comments=[],
                )
            )

            # add core and all scopes
            for shared_action, scope_ctx in scope_ctx_by_action.items():
                for scope_type, scopes in scope_ctx.items():
                    for scope_name in scopes:

                        if scope_name not in scope_graph:
                            node_type_cls = SubroutineNode if scope_type == "raw" else AssymetricNode
                            scope_graph.elements.append(
                                node_type_cls(name=f"{scope_name}:{action}", short=scope_name, comments="")
                            )
                        # link from src:001:sap to 'src:001:sap:rawdb'
                        edge_type_cls = Edge if shared_action == "owner" else DottedEdge
                        graph.edges.append(
                            edge_type_cls(
                                name=group_name, dest=f"{scope_name}:{action}", annotation=shared_action, comments=[]
                            )
                        )

        # namespace-level like cdf:src:all:read
        elif action and group_ns:
            ns_cdf_graph.elements.append(Node(name=group_name, short=group_name, comments=""))

            # link from 'all' to 'src:all'
            edge_type_cls = Edge if action == "owner" else DottedEdge
            graph.edges.append(
                edge_type_cls(
                    name=f"{config.GROUP_NAME_PREFIX}{config.AGGREGATED_GROUP_NAME}:{action}",
                    dest=group_name,
                    annotation="",
                    comments=[],
                )
            )

        # top-level like cdf:all:read
        elif action:
            ns_cdf_graph.elements.append(Node(name=group_name, short=group_name, comments=""))

    # sorting relationship output into potential subgraphs
    graph = GraphRegistry()
    # top subgraphs (three columns)
    aad_group = graph.get_or_create(SubgraphTypes.aad)
    owner = graph.get_or_create(SubgraphTypes.owner)
    read = graph.get_or_create(SubgraphTypes.read)
    core_cdf_owner = graph.get_or_create(SubgraphTypes.core_cdf_owner)
    ns_cdf_owner = graph.get_or_create(SubgraphTypes.ns_cdf_owner)
    core_cdf_read = graph.get_or_create(SubgraphTypes.core_cdf_read)
    ns_cdf_read = graph.get_or_create(SubgraphTypes.ns_cdf_read)
    scope_owner = graph.get_or_create(SubgraphTypes.scope_owner)
    scope_read = graph.get_or_create(SubgraphTypes.scope_read)

    # add the three top level groups to our graph
    graph.elements.extend(
        [
            aad_group,
            owner,
            read,
            # doc_group
        ]
    )
    owner.elements.extend(
        [
            core_cdf_owner,
            ns_cdf_owner,
            scope_owner,
        ]
    )
    read.elements.extend(
        [
            core_cdf_read,
            ns_cdf_read,
            scope_read,
        ]
    )

    # permutate the combinations
    for action in ["read", "owner"]:  # action_dimensions w/o 'admin'
        for group_ns, group_configs in config.group_bootstrap_hierarchy.items():
            for group_core, group_config in group_configs.items():
                # group for each dedicated group-type id
                temp_group(graph, action, group_ns, group_core)
            # 'all' groups on group-type level
            # (access to all datasets/ raw-dbs which belong to this group-type)
            temp_group(graph, action, group_ns)
        # 'all' groups on action level (no limits to datasets or raw-dbs)
        temp_group(graph, action)
    # all (no limits + admin)
    # 211013 pa: for AAD root:client and root:user can be merged into 'root'
    # for root_account in ["root:client", "root:user"]:
    for root_account in ["root"]:
        temp_group(graph, root_account=root_account)

    mermaid_code = graph.to_mermaid(to_markdown)
    print(mermaid_code)
