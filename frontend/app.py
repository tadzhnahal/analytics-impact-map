import streamlit as st
import streamlit.components.v1 as components_html

from api import get_components, get_dependencies, run_analysis
from graph_view import build_graph_html

st.set_page_config(page_title="Analytics Impact Map", layout="wide")
st.title("Analytics Impact Map")
st.write("Frontend MVP for impact analysis")

try:
    components = get_components()
except Exception as e:
    st.error(f"failed to load components: {e}")
    st.stop()

try:
    dependencies = get_dependencies()
except Exception as e:
    st.error(f"failed to load dependencies: {e}")
    st.stop()

if not components:
    st.warning("no components found")
    st.stop()

st.subheader("Components")

table_data = []
for item in components:
    table_data.append(
        {
            "id": item["id"],
            "name": item["name"],
            "type": item["component_type"],
            "description": item["description"],
        }
    )

st.table(table_data)

component_map = {}
for item in components:
    component_map[item["id"]] = item

st.subheader("Dependencies")

dependency_table = []
for item in dependencies:
    source_component = component_map.get(item["source_component_id"])
    target_component = component_map.get(item["target_component_id"])

    dependency_table.append(
        {
            "source_id": item["source_component_id"],
            "source_name": source_component["name"] if source_component else "unknown",
            "target_id": item["target_component_id"],
            "target_name": target_component["name"] if target_component else "unknown",
            "dependency_type": item["dependency_type"],
        }
    )

if dependency_table:
    st.table(dependency_table)
else:
    st.info("No dependencies found")

st.subheader("Dependency map")

graph_html = build_graph_html(components, dependencies)
components_html.html(graph_html, height=560, scrolling=False)

st.subheader("Run analysis")

component_options = {}
for item in components:
    label = f"{item['id']} — {item['name']} ({item['component_type']})"
    component_options[label] = item["id"]

selected_label = st.selectbox(
    "Choose root component",
    list(component_options.keys()),
)

selected_component_id = component_options[selected_label]

if st.button("Run impact analysis"):
    try:
        result = run_analysis(selected_component_id)

        root_component = result["root_component"]
        affected_components = result["affected_components"]
        affected_count = result["affected_count"]

        st.subheader("Analysis result")

        st.write("Root component:")
        st.write(
            {
                "id": root_component["id"],
                "name": root_component["name"],
                "type": root_component["component_type"],
                "description": root_component["description"],
            }
        )

        st.write(f"Affected components: {affected_count}")

        if affected_components:
            affected_table = []

            for item in affected_components:
                affected_table.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "type": item["component_type"],
                        "description": item["description"],
                    }
                )

            st.table(affected_table)
        else:
            st.info("No affected components found")

    except Exception as e:
        st.error(f"failed to run analysis: {e}")