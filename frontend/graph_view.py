from pyvis.network import Network


def get_node_color(component_id, root_id=None, affected_ids=None):
    affected_ids = affected_ids or []

    if root_id is not None and component_id == root_id:
        return "#f4a261"

    if component_id in affected_ids:
        return "#e76f51"

    return "#8ecae6"


def build_graph_html(components, dependencies, root_id=None, affected_ids=None):
    net = Network(height="520px", width="100%", directed=True)

    net.set_options(
        """
        var options = {
          "layout": {
            "improvedLayout": true
          },
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -45,
              "centralGravity": 0.01,
              "springLength": 150,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 0.8
            },
            "stabilization": {
              "enabled": true,
              "iterations": 120,
              "updateInterval": 20
            }
          },
          "interaction": {
            "hover": true,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true,
            "tooltipDelay": 120
          },
          "nodes": {
            "shape": "dot",
            "size": 22,
            "font": {
              "size": 16
            }
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true
              }
            },
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },
            "font": {
              "size": 12,
              "align": "middle"
            }
          }
        }
        """
    )

    affected_ids = affected_ids or []

    for item in components:
        description = item["description"] if item["description"] else "-"
        title = f"type: {item['component_type']}<br>description: {description}"
        color = get_node_color(
            item["id"],
            root_id=root_id,
            affected_ids=affected_ids,
        )

        if item["id"] == root_id:
            border_width = 3
        elif item["id"] in affected_ids:
            border_width = 2
        else:
            border_width = 1

        net.add_node(
            item["id"],
            label=item["name"],
            title=title,
            color=color,
            borderWidth=border_width,
        )

    for item in dependencies:
        net.add_edge(
            item["source_component_id"],
            item["target_component_id"],
            label=item["dependency_type"],
            title=item["dependency_type"],
        )

    return net.generate_html()