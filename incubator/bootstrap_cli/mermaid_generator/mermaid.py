# std-lib
from datetime import datetime
from dataclasses import dataclass

# type-hints
from typing import Dict, List, TypeVar, Type, Union


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

    def to_mermaid(self) -> str:

        mermaid_flowchart = "\n".join(
            (
                ["graph LR", f"%% {timestamp()} - Script generated Mermaid diagram"]
                + list(map(str, self.elements + self.edges))
            )
        )

        return mermaid_flowchart
