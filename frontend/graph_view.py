from streamlit_agraph import agraph, Node, Edge, Config


def get_node_color(component_id, root_id=None, affected_ids=None):
    affected_ids = affected_ids or []

    if root_id is not None and component_id == root_id:
        return "#f4a261"

    if component_id in affected_ids:
        return "#e76f51"

    return "#8ecae6"


def build_graph_nodes(components, root_id=None, affected_ids=None):
    nodes = []
    affected_ids = affected_ids or []

    for item in components:
        color = get_node_color(
            item["id"],
            root_id=root_id,
            affected_ids=affected_ids,
        )

        if item["id"] == root_id:
            size = 34
        elif item["id"] in affected_ids:
            size = 30
        else:
            size = 25

        node = Node(
            id=str(item["id"]),
            label=item["name"],
            size=size,
            color=color,
        )

        nodes.append(node)

    return nodes


def build_graph_edges(dependencies):
    edges = []

    for item in dependencies:
        edge = Edge(
            source=str(item["source_component_id"]),
            target=str(item["target_component_id"]),
            label=item["dependency_type"],
        )

        edges.append(edge)

    return edges


def show_graph(components, dependencies, root_id=None, affected_ids=None):
    nodes = build_graph_nodes(
        components,
        root_id=root_id,
        affected_ids=affected_ids,
    )
    edges = build_graph_edges(dependencies)

    config = Config(
        width="100%",
        height=560,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#f4a261",
        collapsible=False,
    )

    selected_node = agraph(
        nodes=nodes,
        edges=edges,
        config=config,
    )

    return selected_node