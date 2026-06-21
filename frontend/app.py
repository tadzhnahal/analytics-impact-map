import streamlit as st

from api import (get_components, get_dependencies, run_analysis,
                 create_component, create_dependency, delete_component_by_id,
                 delete_dependency_by_id, update_component_by_id,
                 update_dependency_by_id)
from graph_canvas import graph_canvas


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_canvas_nodes(
    components,
    root_id=None,
    affected_ids=None,
    graph_positions=None,
    selected_node_ids=None,
):
    nodes = []
    affected_ids = affected_ids or []
    graph_positions = graph_positions or {}
    selected_node_ids = selected_node_ids or []

    for index, item in enumerate(components):
        status = "normal"

        if root_id is not None and item["id"] == root_id:
            status = "root"
        elif item["id"] in affected_ids:
            status = "affected"

        default_x = 120 + (index % 4) * 220
        default_y = 80 + (index // 4) * 140

        saved_position = graph_positions.get(str(item["id"]))

        if saved_position:
            x = saved_position.get("x", default_x)
            y = saved_position.get("y", default_y)
        else:
            x = default_x
            y = default_y

        nodes.append(
            {
                "id": str(item["id"]),
                "label": item["name"],
                "node_type": item["component_type"],
                "description": item["description"],
                "x": x,
                "y": y,
                "status": status,
                "selected": str(item["id"]) in selected_node_ids,
            }
        )

    return nodes


def build_canvas_edges(dependencies, selected_edge_ids=None):
    edges = []
    selected_edge_ids = selected_edge_ids or []

    for item in dependencies:
        edges.append(
            {
                "id": str(item["id"]),
                "source": str(item["source_component_id"]),
                "target": str(item["target_component_id"]),
                "label": item["dependency_type"],
                "dependency_type": item["dependency_type"],
                "selected": str(item["id"]) in selected_edge_ids,
            }
        )

    return edges


def get_selected_components(selected_node_ids, component_map):
    selected_components = []

    for node_id in selected_node_ids:
        component_id = to_int(node_id)

        if component_id is None:
            continue

        component = component_map.get(component_id)

        if component:
            selected_components.append(component)

    return selected_components


def get_selected_dependency(selected_edge_ids, dependency_map):
    if not selected_edge_ids:
        return None

    dependency_id = to_int(selected_edge_ids[0])

    if dependency_id is None:
        return None

    return dependency_map.get(dependency_id)


def clear_graph_selection():
    st.session_state["selected_node_ids"] = []
    st.session_state["selected_edge_ids"] = []


def create_component_from_canvas(payload):
    name = (payload.get("name") or "").strip()
    component_type = payload.get("component_type") or "other"
    description = (payload.get("description") or "").strip() or None

    if not name:
        st.session_state["canvas_message"] = "Название компонента не должно быть пустым"
        return

    try:
        created_component = create_component(
            name=name,
            component_type=component_type,
            description=description,
        )

        if created_component and "id" in created_component:
            st.session_state["selected_node_ids"] = [str(created_component["id"])]
            st.session_state["selected_edge_ids"] = []

        st.session_state["analysis_result"] = None
        st.session_state["canvas_message"] = "Компонент создан"
        st.rerun()

    except Exception as e:
        st.session_state["canvas_message"] = f"Не удалось создать компонент: {e}"


def create_dependency_from_canvas(payload):
    source_id = to_int(payload.get("source_component_id"))
    target_id = to_int(payload.get("target_component_id"))
    dependency_type = payload.get("dependency_type") or "hard"

    if source_id is None or target_id is None:
        st.session_state["canvas_message"] = "Выберите два компонента"
        return

    if source_id == target_id:
        st.session_state["canvas_message"] = "Компонент не может зависеть сам от себя"
        return

    try:
        create_dependency(
            source_component_id=source_id,
            target_component_id=target_id,
            dependency_type=dependency_type,
        )
        st.session_state["selected_node_ids"] = []
        st.session_state["selected_edge_ids"] = []
        st.session_state["analysis_result"] = None
        st.session_state["canvas_message"] = "Связь создана"
        st.rerun()

    except Exception as e:
        st.session_state["canvas_message"] = f"Не удалось создать связь: {e}"


def run_analysis_from_canvas(node_ids):
    if not node_ids:
        return

    component_id = to_int(node_ids[0])

    if component_id is None:
        return

    try:
        st.session_state["analysis_result"] = run_analysis(component_id)
        st.session_state["selected_node_ids"] = [str(component_id)]
        st.session_state["selected_edge_ids"] = []
        st.session_state["canvas_message"] = "Анализ готов"
        st.rerun()

    except Exception as e:
        st.session_state["canvas_message"] = f"Не удалось запустить анализ: {e}"


def handle_canvas_event(canvas_event):
    if not canvas_event:
        return

    event_type = canvas_event.get("event_type")
    node_ids = canvas_event.get("node_ids") or []
    edge_ids = canvas_event.get("edge_ids") or []
    positions = canvas_event.get("positions") or {}
    payload = canvas_event.get("payload") or {}

    if positions:
        st.session_state["graph_positions"] = positions

    st.session_state["last_canvas_event"] = canvas_event
    st.session_state["last_canvas_event_type"] = event_type

    if event_type == "node_drag_stop":
        return

    if event_type == "create_component":
        create_component_from_canvas(payload)
        return

    if event_type == "create_dependency":
        create_dependency_from_canvas(payload)
        return

    if event_type == "toggle_analysis_mode":
        st.session_state["analysis_mode"] = not st.session_state["analysis_mode"]

        if st.session_state["analysis_mode"]:
            st.session_state["canvas_message"] = "Кликните по узлу для анализа"
        else:
            st.session_state["canvas_message"] = None

        st.rerun()

    if event_type == "reset_layout":
        st.session_state["graph_positions"] = {}
        st.session_state["layout_version"] += 1
        st.session_state["canvas_message"] = "Раскладка сброшена"
        st.rerun()

    if event_type == "run_analysis":
        run_analysis_from_canvas(node_ids)
        return

    if event_type in ["node_click", "node_context_menu"]:
        st.session_state["selected_node_ids"] = node_ids
        st.session_state["selected_edge_ids"] = []

    elif event_type in ["edge_click", "edge_context_menu"]:
        st.session_state["selected_node_ids"] = []
        st.session_state["selected_edge_ids"] = edge_ids

    elif event_type == "pane_click":
        clear_graph_selection()

    elif event_type == "selection_change":
        st.session_state["selected_node_ids"] = node_ids
        st.session_state["selected_edge_ids"] = edge_ids


def show_component_card(component):
    st.markdown(f"### {component['name']}")
    st.write(f"**id:** {component['id']}")
    st.write(f"**тип:** {component['component_type']}")

    if component["description"]:
        st.write(f"**описание:** {component['description']}")
    else:
        st.write("**описание:** -")

    if st.button(
        "Запустить анализ",
        key=f"run_analysis_from_inspector_{component['id']}",
    ):
        try:
            st.session_state["analysis_result"] = run_analysis(component["id"])
            st.rerun()
        except Exception as e:
            st.error(f"Не удалось запустить анализ: {e}")


def show_multiple_components_card(components):
    st.markdown("### Несколько узлов")
    st.write(f"**выбрано:** {len(components)}")

    rows = []

    for item in components:
        rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "type": item["component_type"],
            }
        )

    st.table(rows)


def show_dependency_card(dependency, component_map):
    source_component = component_map.get(dependency["source_component_id"])
    target_component = component_map.get(dependency["target_component_id"])

    source_name = source_component["name"] if source_component else "Неизвестный компонент"
    target_name = target_component["name"] if target_component else "Неизвестный компонент"

    st.markdown("### Связь")
    st.write(f"**id:** {dependency['id']}")
    st.write(f"**откуда:** {source_name}")
    st.write(f"**куда:** {target_name}")
    st.write(f"**тип:** {dependency['dependency_type']}")

    st.caption("Действия со связью добавим через контекстное меню.")


def show_empty_inspector():
    st.info("Кликните по узлу или связи на карте.")

    st.markdown(
        """
        **Подсказки**

        - ЛКМ по узлу выбирает компонент.
        - ЛКМ по связи выбирает зависимость.
        - Зажмите ЛКМ на пустом месте и потяните, чтобы выбрать рамкой.
        - Потяните выбранный узел, чтобы сдвинуть группу.
        - Держите Space и тяните поле, чтобы сдвинуть карту.
        """
    )


st.set_page_config(
    page_title="Аналитическая карта зависимостей",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "selected_node_ids" not in st.session_state:
    st.session_state["selected_node_ids"] = []

if "selected_edge_ids" not in st.session_state:
    st.session_state["selected_edge_ids"] = []

if "last_canvas_event" not in st.session_state:
    st.session_state["last_canvas_event"] = None

if "last_canvas_event_type" not in st.session_state:
    st.session_state["last_canvas_event_type"] = None

if "graph_positions" not in st.session_state:
    st.session_state["graph_positions"] = {}

if "analysis_mode" not in st.session_state:
    st.session_state["analysis_mode"] = False

if "canvas_message" not in st.session_state:
    st.session_state["canvas_message"] = None

if "layout_version" not in st.session_state:
    st.session_state["layout_version"] = 0

try:
    components = get_components()
except Exception as e:
    st.error(f"Не удалось загрузить компоненты: {e}")
    st.stop()

try:
    dependencies = get_dependencies()
except Exception as e:
    st.error(f"Не удалось загрузить зависимости: {e}")
    st.stop()

analysis_result = st.session_state["analysis_result"]

component_map = {}
for item in components:
    component_map[item["id"]] = item

dependency_map = {}
for item in dependencies:
    dependency_map[item["id"]] = item

valid_node_ids = set()
for item in components:
    valid_node_ids.add(str(item["id"]))

valid_edge_ids = set()
for item in dependencies:
    valid_edge_ids.add(str(item["id"]))

st.session_state["selected_node_ids"] = [
    node_id
    for node_id in st.session_state["selected_node_ids"]
    if node_id in valid_node_ids
]

st.session_state["selected_edge_ids"] = [
    edge_id
    for edge_id in st.session_state["selected_edge_ids"]
    if edge_id in valid_edge_ids
]

root_id = None
affected_ids = []

if analysis_result:
    root_id = analysis_result["root_component"]["id"]

    for item in analysis_result["affected_components"]:
        affected_ids.append(item["id"])

with st.sidebar:
    st.header("Запасные действия")

    with st.expander("Редактировать компонент"):
        if components:
            edit_component_options = {}

            for item in components:
                label = f"{item['id']} — {item['name']} ({item['component_type']})"
                edit_component_options[label] = item["id"]

            edit_component_label = st.selectbox(
                "Выберите компонент, чтобы отредактировать",
                list(edit_component_options.keys()),
            )

            edit_component_id = edit_component_options[edit_component_label]
            selected_component = component_map[edit_component_id]

            component_type_options = ["source", "mart", "dashboard", "service", "report", "other"]

            current_type = selected_component["component_type"]
            if current_type not in component_type_options:
                component_type_options.append(current_type)

            current_type_index = component_type_options.index(current_type)

            with st.form("edit_component_form"):
                updated_component_name = st.text_input(
                    "Новое название компонента",
                    value=selected_component["name"],
                )
                updated_component_type = st.selectbox(
                    "Новый тип компонента",
                    component_type_options,
                    index=current_type_index,
                )
                updated_component_description = st.text_area(
                    "Новое описание",
                    value=selected_component["description"] or "",
                    height=80,
                )

                update_component_submit = st.form_submit_button("Сохранить изменения")

            if update_component_submit:
                if not updated_component_name.strip():
                    st.error("Название для компонента не должно быть пустым")
                else:
                    try:
                        update_component_by_id(
                            component_id=edit_component_id,
                            name=updated_component_name.strip(),
                            component_type=updated_component_type,
                            description=updated_component_description.strip() or None,
                        )
                        st.session_state["analysis_result"] = None
                        st.success("Вы успешно обновили компонент")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Не удалось обновить компонент: {e}")

        else:
            st.info("Сначала добавьте хотя бы один компонент")

    with st.expander("Удалить компонент"):
        if components:
            delete_component_options = {}

            for item in components:
                label = f"{item['id']} — {item['name']} ({item['component_type']})"
                delete_component_options[label] = item["id"]

            with st.form("delete_component_form"):
                delete_component_label = st.selectbox(
                    "Компонент для удаления",
                    list(delete_component_options.keys()),
                )
                confirm_delete_component = st.checkbox("Я понимаю, что удаление нельзя отменить")
                delete_component_submit = st.form_submit_button("Удалить компонент")

            if delete_component_submit:
                component_id_to_delete = delete_component_options[delete_component_label]

                if not confirm_delete_component:
                    st.error("Подтвердите удаление компонента")
                else:
                    try:
                        delete_component_by_id(component_id_to_delete)
                        st.session_state["selected_node_ids"] = []
                        st.session_state["selected_edge_ids"] = []
                        st.session_state["analysis_result"] = None
                        st.success("Вы успешно удалили компонент")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Не удалось удалить компонент: {e}")
        else:
            st.info("Сначала добавьте хотя бы один компонент")

    with st.expander("Редактировать зависимость"):
        if dependencies:
            edit_dependency_options = {}
            dependency_map_for_sidebar = {}

            for item in dependencies:
                dependency_map_for_sidebar[item["id"]] = item

                source_component = component_map.get(item["source_component_id"])
                target_component = component_map.get(item["target_component_id"])

                source_name = source_component["name"] if source_component else "Неизвестный компонент"
                target_name = target_component["name"] if target_component else "Неизвестный компонент"

                label = f"{item['id']} — {source_name} -> {target_name} ({item['dependency_type']})"
                edit_dependency_options[label] = item["id"]

            edit_dependency_label = st.selectbox(
                "Выберите зависимость, чтобы отредактировать её",
                list(edit_dependency_options.keys()),
            )

            edit_dependency_id = edit_dependency_options[edit_dependency_label]
            selected_dependency = dependency_map_for_sidebar.get(edit_dependency_id)

            edit_dependency_component_options = {}

            for item in components:
                label = f"{item['id']} — {item['name']} ({item['component_type']})"
                edit_dependency_component_options[label] = item["id"]

            component_labels = list(edit_dependency_component_options.keys())

            current_source_label = None
            current_target_label = None

            for label, component_id in edit_dependency_component_options.items():
                if component_id == selected_dependency["source_component_id"]:
                    current_source_label = label

                if component_id == selected_dependency["target_component_id"]:
                    current_target_label = label

            source_index = component_labels.index(current_source_label)
            target_index = component_labels.index(current_target_label)

            dependency_type_options = ["hard", "soft"]
            current_dependency_type = selected_dependency["dependency_type"]
            dependency_type_index = dependency_type_options.index(current_dependency_type)

            with st.form("edit_dependency_form"):
                updated_source_label = st.selectbox(
                    "Новый исходный компонент",
                    component_labels,
                    index=source_index,
                    key="edit_dependency_source",
                )
                updated_target_label = st.selectbox(
                    "Новый зависимый компонент",
                    component_labels,
                    index=target_index,
                    key="edit_dependency_target",
                )
                updated_dependency_type = st.selectbox(
                    "Новый тип зависимости",
                    dependency_type_options,
                    index=dependency_type_index,
                )

                update_dependency_submit = st.form_submit_button("Сохранить изменения")

            if update_dependency_submit:
                updated_source_id = edit_dependency_component_options[updated_source_label]
                updated_target_id = edit_dependency_component_options[updated_target_label]

                if updated_source_id == updated_target_id:
                    st.error("Компонент не может зависеть сам от себя")
                else:
                    try:
                        update_dependency_by_id(
                            dependency_id=edit_dependency_id,
                            source_component_id=updated_source_id,
                            target_component_id=updated_target_id,
                            dependency_type=updated_dependency_type,
                        )
                        st.session_state["analysis_result"] = None
                        st.success("Вы успешно обновили зависимость")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Не удалось обновить зависимость: {e}")
        else:
            st.info("Сначала добавьте хотя бы одну зависимость")

    with st.expander("Удалить зависимость"):
        if dependencies:
            delete_dependency_options = {}

            for item in dependencies:
                source_component = component_map.get(item["source_component_id"])
                target_component = component_map.get(item["target_component_id"])

                source_name = source_component["name"] if source_component else "Неизвестный компонент"
                target_name = target_component["name"] if target_component else "Неизвестный компонент"

                label = f"{item['id']} — {source_name} -> {target_name} ({item['dependency_type']})"
                delete_dependency_options[label] = item["id"]

            with st.form("delete_dependency_form"):
                delete_dependency_label = st.selectbox(
                    "Выберите зависимость для удаления",
                    list(delete_dependency_options.keys()),
                )
                confirm_delete_dependency = st.checkbox("Я понимаю, что удаление зависимости нельзя отменить")
                delete_dependency_submit = st.form_submit_button("Удалить зависимость")

            if delete_dependency_submit:
                dependency_id_to_delete = delete_dependency_options[delete_dependency_label]

                if not confirm_delete_dependency:
                    st.error("Подтвердите удаление")
                else:
                    try:
                        delete_dependency_by_id(dependency_id_to_delete)
                        st.session_state["selected_edge_ids"] = []
                        st.session_state["analysis_result"] = None
                        st.success("Вы успешно удалили зависимость")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Не удалось удалить зависимость: {e}")
        else:
            st.info("Сначала добавьте хотя бы одну зависимость")

graph_col, inspector_col = st.columns([4, 1])

with graph_col:
    canvas_nodes = build_canvas_nodes(
        components,
        root_id=root_id,
        affected_ids=affected_ids,
        graph_positions=st.session_state["graph_positions"],
        selected_node_ids=st.session_state["selected_node_ids"],
    )
    canvas_edges = build_canvas_edges(
        dependencies,
        selected_edge_ids=st.session_state["selected_edge_ids"],
    )

    canvas_event = graph_canvas(
        nodes=canvas_nodes,
        edges=canvas_edges,
        height=720,
        analysis_mode=st.session_state["analysis_mode"],
        layout_version=st.session_state["layout_version"],
        key="graph_canvas_stage_9_fixed_drag",
    )

    handle_canvas_event(canvas_event)

with inspector_col:
    st.subheader("Проверка")

    if st.session_state["canvas_message"]:
        st.info(st.session_state["canvas_message"])

    selected_components = get_selected_components(
        st.session_state["selected_node_ids"],
        component_map,
    )
    selected_dependency = get_selected_dependency(
        st.session_state["selected_edge_ids"],
        dependency_map,
    )

    if selected_dependency:
        show_dependency_card(selected_dependency, component_map)

    elif len(selected_components) == 1:
        show_component_card(selected_components[0])

    elif len(selected_components) > 1:
        show_multiple_components_card(selected_components)

    else:
        show_empty_inspector()

    with st.expander("Debug события"):
        if st.session_state["last_canvas_event"]:
            st.json(st.session_state["last_canvas_event"])
        else:
            st.write("Событий пока нет")

if analysis_result:
    root_component = analysis_result["root_component"]
    affected_components = analysis_result["affected_components"]
    affected_count = analysis_result["affected_count"]

    with st.expander("Результат анализа", expanded=True):
        root_table = [
            {
                "id": root_component["id"],
                "name": root_component["name"],
                "type": root_component["component_type"],
                "description": root_component["description"],
            }
        ]

        st.write("Корневой узел:")
        st.table(root_table)

        st.write(f"Затронутые компоненты: {affected_count}")

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
            st.info("Затронутых компонентов нет")

with st.expander("Показать все компоненты"):
    if components:
        components_table = []

        for item in components:
            components_table.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["component_type"],
                    "description": item["description"],
                }
            )

        st.table(components_table)
    else:
        st.info("Компонентов пока нет")

with st.expander("Показать зависимости"):
    dependency_table = []

    for item in dependencies:
        source_component = component_map.get(item["source_component_id"])
        target_component = component_map.get(item["target_component_id"])

        dependency_table.append(
            {
                "source_id": item["source_component_id"],
                "source_name": source_component["name"] if source_component else "Неизвестный компонент",
                "target_id": item["target_component_id"],
                "target_name": target_component["name"] if target_component else "Неизвестный компонент",
                "dependency_type": item["dependency_type"],
            }
        )

    if dependency_table:
        st.table(dependency_table)
    else:
        st.info("Зависимостей пока нет")
