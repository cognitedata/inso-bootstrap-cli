import logging
from enum import Enum
from typing import Any, Dict, Tuple

from ..app_config import AclDefaultTypes, RoleType, ScopeCtxType, YesNoType
from .base import CommandBase
from .diagram_utils.mermaid import (
    AssymetricNode,
    DottedEdge,
    Edge,
    GraphRegistry,
    HexagonNode,
    Node,
    RoundedEdgesNode,
    SubroutineNode,
    TrapezoidAltNode,
)


class CommandDiagram(CommandBase):

    # '''
    #        .o8   o8o
    #       "888   `"'
    #   .oooo888  oooo   .oooo.    .oooooooo oooo d8b  .oooo.   ooo. .oo.  .oo.
    #  d88' `888  `888  `P  )88b  888' `88b  `888""8P `P  )88b  `888P"Y88bP"Y88b
    #  888   888   888   .oP"888  888   888   888      .oP"888   888   888   888
    #  888   888   888  d8(  888  `88bod8P'   888     d8(  888   888   888   888
    #  `Y8bod88P" o888o `Y888""8o `8oooooo.  d888b    `Y888""8o o888o o888o o888o
    #                             d"     YD
    #                             "Y88888P'
    # '''

    def command(
        self,
        to_markdown: YesNoType = YesNoType.no,
        with_raw_capability: YesNoType = YesNoType.yes,
        cdf_project: str = None,
    ) -> None:
        """Diagram mode used to document the given configuration as a Mermaid diagram.

        Args:
            to_markdown (YesNoType, optional):
              - Encapsulate Mermaid diagram in Markdown syntax.
              - Defaults to 'YesNoType.no'.
            with_raw_capability (YesNoType, optional):
              - Create RAW DBs and 'rawAcl' capability. Defaults to 'YesNoType.tes'.
            cdf_project (str, optional):
              - Provide the CDF Project to use for the diagram 'idp-cdf-mappings'.

        Example:
            # requires a 'cognite' configuration section
            ➟  poetry run bootstrap-cli diagram configs/config-deploy-example-v2.yml | clip.exe
            # precedence over 'cognite.project' which CDF Project to diagram 'bootstrap.idp-cdf-mappings'
            # making a 'cognite' section optional
            ➟  poetry run bootstrap-cli diagram --cdf-project shiny-dev configs/config-deploy-example-v2.yml | clip.exe
            # precedence over configuration 'bootstrap.features.with-raw-capability'
            ➟  poetry run bootstrap-cli diagram --with-raw-capability no --cdf-project shiny-prod configs/config-deploy-example-v2.yml
        """  # noqa

        # availability is validate_cdf_project_available()
        diagram_cdf_project = cdf_project or self.cdf_project

        # same handling as in 'deploy' command
        # store parameter as bool
        # if available it overrides configuration or defaults from yaml-config
        if with_raw_capability:
            self.with_raw_capability = with_raw_capability == YesNoType.yes

        # debug new features and override with cli-parameters
        logging.info(
            "'diagram' configured for CDF Project: "
            f"<{diagram_cdf_project}> and 'with_raw_capability': {self.with_raw_capability}"
        )

        # store all raw_dbs and datasets in scope of this configuration
        # TODO: wrong structure, actions (RoleType) are added by get_scope_ctx_groupedby_action(..)
        # diagram uses this data different then deploy
        self.all_scoped_ctx = {
            RoleType.OWNER: (
                all_scopes := {
                    # generate_target_raw_dbs -> returns a Set[str]
                    ScopeCtxType.RAWDB: list(self.generate_target_raw_dbs()),  # all raw_dbs
                    # generate_target_datasets -> returns a Dict[str, Any]
                    ScopeCtxType.DATASET: list(self.generate_target_datasets().keys()),  # all datasets
                }
            ),
            # and copy the same to 'read'
            RoleType.READ: all_scopes,
        }

        def scopectx_mermaid_node_mapping(scopectx: ScopeCtxType) -> Node:
            # hide a dict access in this typed-helper method
            return {
                ScopeCtxType.DATASET: AssymetricNode,
                ScopeCtxType.RAWDB: SubroutineNode,
                ScopeCtxType.SPACE: HexagonNode,
            }[scopectx]

        def get_group_name_and_scopes(
            action: str = None, ns_name: str = None, node_name: str = None, root_account: str = None
        ) -> Tuple[str, Dict[str, Any]]:
            """Adopted generate_group_name_and_capabilities() and get_scope_ctx_groupedby_action()
            to respond with
            - the full-qualified CDF group name and
            - all scopes sorted by action [read|owner] and [raw|datasets]

            Args:
                action (str, optional):
                    One of the action_dimensions [RoleType.READ, RoleType.OWNER].
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
                    Tuple[str, Dict[str, Any]]: (group_name, scope_ctx_by_action)
                        scope_ctx_by_action is a dictionary with the following structure:
                            {RoleType.OWNER: {
                                ScopeCtxType.RAWDB: ['src:002:weather:rawdb', 'src:002:weather:rawdb:state'],
                                ScopeCtxType.DATASET: ['src:002:weather:dataset'],
                                ScopeCtxType.SPACE: ['src-002-weather-space'],
                                },
                            RoleType.READ: {
                                ScopeCtxType.RAWDB: [],
                                ScopeCtxType.DATASET: []
                                ScopeCtxType.SPACE: [],
                            }}
            """

            group_name_full_qualified, scope_ctx_by_action = None, None

            # detail level like cdf:src:001:public:read
            if action and ns_name and node_name:
                group_name_full_qualified = f"{CommandBase.GROUP_NAME_PREFIX}{node_name}:{action}"
                scope_ctx_by_action = self.get_scope_ctx_groupedby_action(action, ns_name, node_name)

            # group-type level like cdf:src:all:read
            elif action and ns_name:
                # 'all' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                group_name_full_qualified = (
                    f"{CommandBase.GROUP_NAME_PREFIX}{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}:{action}"  # noqa
                )
                scope_ctx_by_action = self.get_scope_ctx_groupedby_action(action, ns_name)

            # top level like cdf:all:read
            elif action:
                # 'all' groups on action level (no limits to datasets or raw-dbs)
                group_name_full_qualified = (
                    f"{CommandBase.GROUP_NAME_PREFIX}{CommandBase.AGGREGATED_LEVEL_NAME}:{action}"
                )
                # limit all_scopes to 'action'
                scope_ctx_by_action = {action: self.all_scoped_ctx[action]}
            # root level like cdf:root
            elif root_account:  # no parameters
                # all (no limits)
                group_name_full_qualified = f"{CommandBase.GROUP_NAME_PREFIX}{root_account}"

            return group_name_full_qualified, scope_ctx_by_action

        class SubgraphTypes(str, Enum):
            idp = "IdP Groups"
            owner = "'Owner' Groups"
            read = "'Read' Groups"
            # OWNER
            core_cdf_owner = "Node Level (Owner)"
            ns_cdf_owner = "Namespace Level (Owner)"
            scope_owner = "Scopes (Owner)"
            # READ
            core_cdf_read = "Node Level (Read)"
            ns_cdf_read = "Namespace Level (Read)"
            scope_read = "Scopes (Read)"

        # TODO: refactoring required, too much lines
        def group_to_graph(
            graph: GraphRegistry,
            action: str = None,
            ns_name: str = None,
            node_name: str = None,
            root_account: str = None,
        ) -> None:

            if root_account:
                return

            group_name, scope_ctx_by_action = get_group_name_and_scopes(action, ns_name, node_name, root_account)

            # check lookup from provided config
            mapping = self.bootstrap_config.get_idp_cdf_mapping_for_group(
                # diagram explicit given cdf_project, or configured in 'cognite' configuration section
                cdf_project=diagram_cdf_project,
                cdf_group=group_name,
            )
            # unpack
            # idp_source_id, idp_source_name = self.aad_mapping_lookup.get(node_name, [None, None])
            idp_source_id, idp_source_name = mapping.idp_source_id, mapping.idp_source_name

            logging.info(f"{ns_name=} : {group_name=} : {scope_ctx_by_action=} [{idp_source_name=}]")

            # preload master subgraphs
            core_cdf = graph.get_or_create(getattr(SubgraphTypes, f"core_cdf_{action}"))
            ns_cdf_graph = graph.get_or_create(getattr(SubgraphTypes, f"ns_cdf_{action}"))
            scope_graph = graph.get_or_create(getattr(SubgraphTypes, f"scope_{action}"))

            #
            # NODE - IDP GROUP
            #
            idp = graph.get_or_create(SubgraphTypes.idp)
            if idp_source_name and (idp_source_name not in idp):
                idp.elements.append(
                    TrapezoidAltNode(
                        id_name=idp_source_name,
                        display=idp_source_name,
                        comments=[f'IdP objectId: {idp_source_id}']
                    )
                )  # fmt: skip
                graph.edges.append(
                    Edge(
                        id_name=idp_source_name,
                        dest=group_name,
                        annotation=None,
                        comments=[]
                    )
                )  # fmt: skip

            # {'owner': {'raw': ['src:002:weather:rawdb', 'src:002:weather:rawdb:state'],
            #       'datasets': ['src:002:weather:dataset']},
            # 'read': {'raw': [], 'datasets': []}}

            #
            # NODE - CORE LEVEL
            #   'cdf:src:001:public:read'
            #
            if action and ns_name and node_name:
                core_cdf.elements.append(
                    RoundedEdgesNode(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                    )
                )  # fmt: skip

                #
                # EDGE FROM PARENT 'src:all' to 'src:001:sap'
                #
                edge_type_cls = Edge if action == RoleType.OWNER else DottedEdge
                graph.edges.append(
                    edge_type_cls(
                        # link from all:{ns}
                        # multiline f-string split as it got too long
                        # TODO: refactor into string-templates
                        id_name=f"{CommandBase.GROUP_NAME_PREFIX}{ns_name}:"
                        f"{CommandBase.AGGREGATED_LEVEL_NAME}:{action}",
                        dest=group_name,
                        annotation="",
                        comments=[],
                    )
                )  # fmt: skip

                # add core and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type in (ScopeCtxType.RAWDB, ScopeCtxType.SPACE):
                            continue  # for simple diagram SKIP RAW and SPACE

                        if not self.with_datamodel_capability and scope_type == ScopeCtxType.SPACE:
                            continue  # SKIP SPACE

                        for scope_name in scopes:

                            #
                            # NODE DATASET or RAW scope
                            #    'src:001:sap:rawdb'
                            #
                            if scope_name not in scope_graph:
                                node_type_cls = scopectx_mermaid_node_mapping(scope_type)
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                    )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:src:001:sap:read to 'src:001:sap:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == RoleType.OWNER else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

            #
            # NODE - NAMESPACE LEVEL
            #   'src:all:read' or 'src:all:owner'
            elif action and ns_name:
                ns_cdf_graph.elements.append(
                    Node(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                    )
                )  # fmt: skip

                #
                # EDGE FROM PARENT top LEVEL to NAMESPACE LEVEL
                #   'all' to 'src:all'
                #
                edge_type_cls = Edge if action == RoleType.OWNER else DottedEdge
                graph.edges.append(
                    edge_type_cls(
                        id_name=f"{CommandBase.GROUP_NAME_PREFIX}{CommandBase.AGGREGATED_LEVEL_NAME}:{action}", # noqa
                        dest=group_name,
                        annotation="",
                        comments=[],
                    )
                )  # fmt: skip

                # add namespace-node and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type in (ScopeCtxType.RAWDB, ScopeCtxType.SPACE):
                            continue  # for simple diagram SKIP RAW and SPACE

                        if not self.with_datamodel_capability and scope_type == ScopeCtxType.SPACE:
                            continue  # SKIP SPACE

                        for scope_name in scopes:

                            # LIMIT only to direct scopes for readability
                            # which have for example 'src:all:' as prefix
                            if not scope_name.startswith(f"{ns_name}:{CommandBase.AGGREGATED_LEVEL_NAME}:"):
                                continue

                            #
                            # NODE DATASET or RAW scope
                            #    'src:all:rawdb'
                            #
                            if scope_name not in scope_graph:

                                node_type_cls = scopectx_mermaid_node_mapping(scope_type)
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                    )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:src:all:read to 'src:all:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == RoleType.OWNER else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

            #
            # NODE - TOP LEVEL
            #   like `cdf:all:read`
            #
            elif action:
                ns_cdf_graph.elements.append(
                    Node(
                        id_name=group_name,
                        display=group_name,
                        comments=""
                    )
                )  # fmt: skip

                # add namespace-node and all scopes
                # shared_action: [read|owner]
                for shared_action, scope_ctx in scope_ctx_by_action.items():
                    # scope_type: [raw|datasets]
                    # scopes: List[str]
                    for scope_type, scopes in scope_ctx.items():

                        if not self.with_raw_capability and scope_type in (ScopeCtxType.RAWDB, ScopeCtxType.SPACE):
                            continue  # for simple diagram SKIP RAW and SPACE

                        if not self.with_datamodel_capability and scope_type == ScopeCtxType.SPACE:
                            continue  # SKIP SPACE

                        for scope_name in scopes:

                            # LIMIT only to direct scopes for readability
                            # which have for example 'src:all:' as prefix
                            if not scope_name.startswith(f"{CommandBase.AGGREGATED_LEVEL_NAME}:"):
                                continue

                            # logging.info(f"> {action=} {shared_action=} process {scope_name=} : all {scopes=}")
                            #
                            # NODE DATASET or RAW scope
                            #    'all:rawdb'
                            #
                            if scope_name not in scope_graph:

                                # logging.info(f">> add {scope_name=}__{action=}")

                                node_type_cls = scopectx_mermaid_node_mapping(scope_type)
                                scope_graph.elements.append(
                                    node_type_cls(
                                        id_name=f"{scope_name}__{action}__{scope_type}",
                                        display=scope_name,
                                        comments=""
                                    )
                                )  # fmt: skip

                            #
                            # EDGE FROM actual processed group-node to added scope
                            #   cdf:all:read to 'all:rawdb'
                            #
                            edge_type_cls = Edge if shared_action == RoleType.OWNER else DottedEdge
                            graph.edges.append(
                                edge_type_cls(
                                    id_name=group_name,
                                    dest=f"{scope_name}__{action}__{scope_type}",
                                    annotation=shared_action,
                                    comments=[],
                                )
                            )  # fmt: skip

        #
        # finished inline helper-methods
        # starting diagram logic
        #

        if not self.with_raw_capability:
            # no RAW DBs means no access to RAW at all
            # which means no 'rawAcl' capability to create
            # remove it form the default types
            logging.info("Without RAW_DBS and 'rawAcl' capability")
            AclDefaultTypes.remove("raw")

        # sorting relationship output into potential subgraphs
        graph = GraphRegistry()
        # top subgraphs (three columns layout)
        # provide Subgraphs with a 'subgraph_name' and a 'subgraph_short_name'
        # using the SubgraphTypes enum 'name' (default) and 'value' properties
        idp_group = graph.get_or_create(
            SubgraphTypes.idp, f"{SubgraphTypes.idp.value} for CDF: '{diagram_cdf_project}'"
        )
        owner = graph.get_or_create(SubgraphTypes.owner, SubgraphTypes.owner.value)
        read = graph.get_or_create(SubgraphTypes.read, SubgraphTypes.read.value)

        # nested subgraphs
        core_cdf_owner = graph.get_or_create(SubgraphTypes.core_cdf_owner, SubgraphTypes.core_cdf_owner.value)
        ns_cdf_owner = graph.get_or_create(SubgraphTypes.ns_cdf_owner, SubgraphTypes.ns_cdf_owner.value)
        core_cdf_read = graph.get_or_create(SubgraphTypes.core_cdf_read, SubgraphTypes.core_cdf_read.value)
        ns_cdf_read = graph.get_or_create(SubgraphTypes.ns_cdf_read, SubgraphTypes.ns_cdf_read.value)
        scope_owner = graph.get_or_create(SubgraphTypes.scope_owner, SubgraphTypes.scope_owner.value)
        scope_read = graph.get_or_create(SubgraphTypes.scope_read, SubgraphTypes.scope_read.value)

        # add the three top level groups to our graph
        graph.elements.extend(
            [
                idp_group,
                owner,
                read,
                # doc_group
            ]
        )
        # add/nest the owner-subgraphs to its parent subgraph
        owner.elements.extend(
            [
                core_cdf_owner,
                ns_cdf_owner,
                scope_owner,
            ]
        )
        # add/nest the read-subgraphs to its parent subgraph
        read.elements.extend(
            [
                core_cdf_read,
                ns_cdf_read,
                scope_read,
            ]
        )

        # permutate the combinations
        for action in [RoleType.READ, RoleType.OWNER]:  # action_dimensions w/o 'admin'
            for ns in self.bootstrap_config.namespaces:
                for ns_node in ns.ns_nodes:
                    # group for each dedicated group-type id
                    group_to_graph(graph, action, ns.ns_name, ns_node.node_name)
                # 'all' groups on group-type level
                # (access to all datasets/ raw-dbs which belong to this group-type)
                group_to_graph(graph, action, ns.ns_name)
            # 'all' groups on action level (no limits to datasets or raw-dbs)
            group_to_graph(graph, action)
        # all (no limits + admin)
        # 211013 pa: for AAD root:client and root:user can be merged into 'root'
        # for root_account in ["root:client", "root:user"]:
        for root_account in ["root"]:
            group_to_graph(graph, root_account=root_account)

        mermaid_code = graph.to_mermaid()

        logging.info(f"Generated {len(mermaid_code)} characters")

        markdown_wrapper_template = """
## auto-generated by bootstrap-cli
```mermaid
{mermaid_code}
```"""
        # print to stdout that only the diagram can be piped to clipboard or file
        print(
            markdown_wrapper_template.format(mermaid_code=mermaid_code)
            if to_markdown == YesNoType.yes
            else mermaid_code
        )
