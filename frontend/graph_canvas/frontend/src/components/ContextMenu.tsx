import React from "react";

export type ContextMenuTargetType = "pane" | "node" | "edge";

export type ContextMenuState = {
  isOpen: boolean;
  targetType: ContextMenuTargetType;
  x: number;
  y: number;
  targetId?: string;
  label?: string;
};

type ContextMenuProps = {
  menu: ContextMenuState;
  canCreateDependency: boolean;

  onClose: () => void;
  onRunAnalysis: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onCreateDependencyFromNode: () => void;
  onCreateComponent: () => void;
  onResetLayout: () => void;
  onToggleDependencyType: () => void;
};

function ContextMenu(props: ContextMenuProps) {
  if (!props.menu.isOpen) {
    return null;
  }

  return (
    <div
      className="graph-context-menu"
      style={{
        left: props.menu.x,
        top: props.menu.y
      }}
      onClick={(event) => event.stopPropagation()}
      onMouseDown={(event) => event.stopPropagation()}
      onContextMenu={(event) => event.preventDefault()}
    >
      {props.menu.targetType === "node" && (
        <>
          <div className="graph-context-title">
            Компонент: {props.menu.label}
          </div>

          <button type="button" onClick={props.onRunAnalysis}>
            Запустить анализ
          </button>

          <button type="button" onClick={props.onEdit}>
            Редактировать
          </button>

          <button
            type="button"
            onClick={props.onCreateDependencyFromNode}
            disabled={!props.canCreateDependency}
          >
            Создать связь отсюда
          </button>

          <div className="graph-context-separator" />

          <button
            type="button"
            className="graph-context-danger"
            onClick={props.onDelete}
          >
            Удалить
          </button>
        </>
      )}

      {props.menu.targetType === "edge" && (
        <>
          <div className="graph-context-title">
            Связь: {props.menu.label}
          </div>

          <button type="button" onClick={props.onEdit}>
            Редактировать
          </button>

          <button type="button" onClick={props.onToggleDependencyType}>
            Сменить hard / soft
          </button>

          <div className="graph-context-separator" />

          <button
            type="button"
            className="graph-context-danger"
            onClick={props.onDelete}
          >
            Удалить
          </button>
        </>
      )}

      {props.menu.targetType === "pane" && (
        <>
          <div className="graph-context-title">
            Canvas
          </div>

          <button type="button" onClick={props.onCreateComponent}>
            Создать компонент
          </button>

          <button type="button" onClick={props.onResetLayout}>
            Сбросить раскладку
          </button>
        </>
      )}

      <div className="graph-context-separator" />

      <button type="button" onClick={props.onClose}>
        Закрыть
      </button>
    </div>
  );
}

export default ContextMenu;
