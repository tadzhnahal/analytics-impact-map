import streamlit as st

from api import get_components, run_analysis

st.set_page_config(page_title="Analytics Impact Map", layout="wide")
st.title("Analytics Impact Map")
st.write("Frontend MVP for impact analysis")

try:
    components = get_components()
except Exception as e:
    st.error(f"failed to load components: {e}")
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