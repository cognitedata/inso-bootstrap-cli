# std-lib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# type-hints
from typing import Dict, List, Type, TypeVar, Union


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

# '''
#       888          888                      888
#       888          888                      888
#       888          888                      888
#   .d88888  8888b.  888888  8888b.   .d8888b 888  8888b.  .d8888b  .d8888b
#  d88" 888     "88b 888        "88b d88P"    888     "88b 88K      88K
#  888  888 .d888888 888    .d888888 888      888 .d888888 "Y8888b. "Y8888b.
#  Y88b 888 888  888 Y88b.  888  888 Y88b.    888 888  888      X88      X88
#   "Y88888 "Y888888  "Y888 "Y888888  "Y8888P 888 "Y888888  88888P'  88888P'
# '''


@dataclass
class MermaidFlowchartElement:
    id_name: str
    # TODO: ading default_factory value, will break the code
    # see https://stackoverflow.com/q/51575931/1104502
    comments: List[str]

    # dump comments
    def comments_to_mermaid(self):
        return f"""{NEWLINE.join([f'%% {comment}' for comment in self.comments]) + NEWLINE}""" if self.comments else ""


# https://mermaid-js.github.io/mermaid/#/flowchart?id=node-shapestyle-and-arrowstyle
@dataclass
class Node(MermaidFlowchartElement):
    display: str

    def __repr__(self):
        # TODO: how to add comments from super class the right way?
        return self.comments_to_mermaid() + f"""{self.id_name}""" + (rf"""["{self.display}"]""" if self.display else "")


@dataclass
class HexagonNode(Node):
    def __repr__(self):
        return (
            self.comments_to_mermaid() + f"""{self.id_name}""" + (rf"""{{"{self.display}"}}""" if self.display else "")
        )


@dataclass
class RoundedNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.id_name}""" + (rf"""("{self.display}")""" if self.display else "")


@dataclass
class TrapezNode(Node):
    def __repr__(self):
        return (
            self.comments_to_mermaid() + f"""{self.id_name}""" + (rf"""[\"{self.display}"/]""" if self.display else "")
        )


@dataclass
class AssymetricNode(Node):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.id_name}""" + (rf""">"{self.display}"]""" if self.display else "")


@dataclass
class SubroutineNode(Node):
    def __repr__(self):
        return (
            self.comments_to_mermaid() + f"""{self.id_name}""" + (rf"""[["{self.display}"]]""" if self.display else "")
        )


@dataclass
class Edge(MermaidFlowchartElement):
    # from / to cannot be used as "from" is a reserved keyword
    dest: str
    annotation: str

    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.id_name}-->{self.dest}"""
        # cannot render a 🕑 on an edge annotation
        # return (
        #     rf'''{self.name}-->|{self.annotation}|{self.dest}'''
        #     if self.annotation
        #     else f'''{self.name}-->{self.dest}'''
        #     )


@dataclass
class DottedEdge(Edge):
    def __repr__(self):
        return self.comments_to_mermaid() + f"""{self.id_name}-.->{self.dest}"""


# type-hint for ExtpipesCore instance response
T_Subgraph = TypeVar("T_Subgraph", bound="Subgraph")


@dataclass
class Subgraph(MermaidFlowchartElement):

    display: str
    elements: List[Union[T_Subgraph, Node]]

    def __contains__(self, name):
        return name in [elem.id_name for elem in self.elements]

    def __getitem__(self, name):
        if name in self.elements:
            return [elem.id_name for elem in self.elements if elem.id_name == name][0]  # exactly one expected

    def __repr__(self):
        return (
            self.comments_to_mermaid()
            # supporting subgraph id and short-name syntax
            # https://mermaid-js.github.io/mermaid/#/flowchart?id=subgraphs
            + f"""
subgraph "{self.id_name}" ["{self.display if self.display else self.id_name}"]
{NEWLINE.join([f'  {elem}' for elem in self.elements])}
end
"""
        )


# '''
#   .d8888b.                           888      8888888b.                   d8b          888
#  d88P  Y88b                          888      888   Y88b                  Y8P          888
#  888    888                          888      888    888                               888
#  888        888d888 8888b.  88888b.  88888b.  888   d88P .d88b.   .d88b.  888 .d8888b  888888 888d888 888  888
#  888  88888 888P"      "88b 888 "88b 888 "88b 8888888P" d8P  Y8b d88P"88b 888 88K      888    888P"   888  888
#  888    888 888    .d888888 888  888 888  888 888 T88b  88888888 888  888 888 "Y8888b. 888    888     888  888
#  Y88b  d88P 888    888  888 888 d88P 888  888 888  T88b Y8b.     Y88b 888 888      X88 Y88b.  888     Y88b 888
#   "Y8888P88 888    "Y888888 88888P"  888  888 888   T88b "Y8888   "Y88888 888  88888P'  "Y888 888      "Y88888
#                             888                                       888                                  888
#                             888                                  Y8b d88P                             Y8b d88P
#                             888                                   "Y88P"                               "Y88P"
# '''
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

    def get_or_create(self, subgraph_name, subgraph_short_name=None):
        return self.subgraph_registry.setdefault(
            # get if exists
            subgraph_name,
            # create if new
            Subgraph(id_name=subgraph_name.name, display=subgraph_short_name, elements=[], comments=[])
            if isinstance(subgraph_name, Enum)
            else Subgraph(id_name=subgraph_name, elements=[], comments=[]),
        )

    #     def __str__(self):
    #         for elem in self.elements:
    #             print(elem.name)

    def to_mermaid(self) -> str:

        mermaid_flowchart = "\n".join(
            (
                ["graph LR", f"%% {timestamp()} - Script generated Mermaid diagram"]
                + list(map(
                    str,
                    # elements of cls 'Subgraph', will dump themselves recursively
                    self.elements
                    + [f"%% all {len(self.edges)} links connecting the above nodes"]
                    + self.edges
                ))  # fmt: skip
            )
        )

        return mermaid_flowchart
