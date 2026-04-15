import streamlit as st
import streamlit.components.v1 as components_html

from api import get_components, get_dependencies, run_analysis, create_component, create_dependency
from graph_view import build_graph_html

st.set_page_config(page_title="Аналитическая карта зависимостей", layout="wide")
st.title("Аналитическая карта зависимостей")
st.caption("Карта показывает, как отказ одного узла влияет на связанные компоненты.")

with st.expander("Помощь"):
    st.markdown(
        """
        **Что показывает карта**
        
        Зависимости между аналитическими компонентами, например, источниками данных,
        витринами и дашбордами.
        
        **Как читать карту**
        - стрелка показывает направление зависимости;
        - если узел A ведёт в узел B, значит, B зависит от A;
        - если источник ломается, система показывает, какие узлы это затронет.
        
        **Как пользоваться картой**
        1. Выберите корневой узел.
        2. Запустите анализ.
        3. Посмотрите подсветку на карте и список затронутых компонентов.
        
        **Цвета на карте**
        - оранжевый: выбранный корневой узел;
        - красный: затронутый узел;
        - голубой: обычный узел.
        """
    )

legend_col_1, legend_col_2, legend_col_3 = st.columns(3)

with legend_col_1:
    st.caption("Корневой узел - оранжевый")

with legend_col_2:
    st.caption("Затронутый узел - красный")

with legend_col_3:
    st.caption("Обычный узел - голубой")

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

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

with st.expander("Добавить новый компонент"):
    with st.form("create_component_form"):
        new_component_name = st.text_input("Название компонента")
        new_component_type = st.selectbox(
            "Тип компонента",
            ["source", "mart", "dashboard", "service", "report", "other"],
        )
        new_component_description = st.text_area("Описание", height=80)

        create_component_submit = st.form_submit_button("Добавить компонент")

    if create_component_submit:
        if not new_component_name.strip():
            st.error("Название компонента не должно быть пустым")
        else:
            try:
                create_component(
                    name=new_component_name.strip(),
                    component_type=new_component_type,
                    description=new_component_description.strip() or None,
                )
                st.success("Компонент успешно добавлен")
                st.rerun()
            except Exception as e:
                st.error(f"Не удалось добавить компонент: {e}")

with st.expander("Добавить новую зависимость"):
    if len(components) < 2:
        st.info("Для создания зависимости нужно минимум два компонента")
    else:
        dependency_component_options = {}

        for item in components:
            label = f"{item['id']} — {item['name']} ({item['component_type']})"
            dependency_component_options[label] = item["id"]

        with st.form("create_dependency_form"):
            source_label = st.selectbox(
                "Исходный компонент",
                list(dependency_component_options.keys()),
                key="dependency_source"
            )
            target_label = st.selectbox(
                "Зависимый компонент",
                list(dependency_component_options.keys()),
                key="dependency_target"
            )
            new_dependency_type = st.selectbox(
                "Тип зависимости",
                ["hard", "soft"]
            )

            create_dependency_submit = st.form_submit_button("Добавить зависимость")

        if create_dependency_submit:
            source_id = dependency_component_options[source_label]
            target_id = dependency_component_options[target_label]

            if source_id == target_id:
                st.error("Компонент не может зависеть сам от себя")
            else:
                try:
                    create_dependency(
                        source_component_id=source_id,
                        target_component_id=target_id,
                        dependency_type=new_dependency_type,
                    )
                    st.success("Зависимость успешно добавлена")
                    st.rerun()
                except Exception as e:
                    st.error(f"Не удалось добавить зависимость: {e}")

if not components:
    st.warning("Компоненты пока не добавлены")
    st.stop()

component_map = {}
for item in components:
    component_map[item["id"]] = item

st.subheader("Карта зависимостей")

analysis_result = st.session_state["analysis_result"]

root_id = None
affected_ids = []

if analysis_result:
    root_id = analysis_result["root_component"]["id"]

    for item in analysis_result["affected_components"]:
        affected_ids.append(item["id"])

graph_html = build_graph_html(
    components,
    dependencies,
    root_id=root_id,
    affected_ids=affected_ids,
)
components_html.html(graph_html, height=560, scrolling=False)

st.subheader("Анализ влияния")

component_options = {}
for item in components:
    label = f"{item['id']} — {item['name']} ({item['component_type']})"
    component_options[label] = item["id"]

selected_label = st.selectbox(
    "Выберите корневой узел",
    list(component_options.keys()),
)

selected_component_id = component_options[selected_label]

if st.button("Запустить анализ влияния"):
    try:
        st.session_state["analysis_result"] = run_analysis(selected_component_id)
    except Exception as e:
        st.session_state["analysis_result"] = None
        st.error(f"Не удалось запустить анализ: {e}")

analysis_result = st.session_state["analysis_result"]

if analysis_result:
    root_component = analysis_result["root_component"]
    affected_components = analysis_result["affected_components"]
    affected_count = analysis_result["affected_count"]

    st.subheader("Результат анализа")

    st.write("Корневой узел:")
    st.write(
        {
            "id": root_component["id"],
            "name": root_component["name"],
            "type": root_component["component_type"],
            "description": root_component["description"],
        }
    )

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

with st.expander("Показать компоненты"):
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

with st.expander("Показать зависимости"):
    dependency_table = []

    for item in dependencies:
        source_component = component_map.get(item["source_component_id"])
        target_component = component_map.get(item["target_component_id"])

        dependency_table.append(
            {
                "source_id": item["source_component_id"],
                "source_name": source_component["name"] if source_component else "неизвестный",
                "target_id": item["target_component_id"],
                "target_name": target_component["name"] if target_component else "неизвестный",
                "dependency_type": item["dependency_type"],
            }
        )

    if dependency_table:
        st.table(dependency_table)
    else:
        st.info("Зависимостей пока нет")